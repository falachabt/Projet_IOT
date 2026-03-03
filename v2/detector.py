"""
Moteur de détection : bouteille, bouchon, étiquette.

Stratégie :
  1. YOLO préentraîné (COCO) → détection « bottle »
  2. Zone haute de la bouteille → heuristique OpenCV pour le bouchon
  3. Zone corps de la bouteille → heuristique OpenCV pour l'étiquette

Retour :
  - dict JSON-sérialisable avec les statuts
  - image annotée (numpy BGR)
"""

from __future__ import annotations

import os
import time
import json
import base64
from datetime import datetime
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

from v2.config import (
    YOLO_MODEL_PATH,
    YOLO_CONFIDENCE,
    YOLO_BOTTLE_CLASS,
    CAP_ZONE_RATIO,
    CAP_EDGE_DENSITY_THRESH,
    CAP_COLOR_VAR_THRESH,
    CAP_MIN_CONTOUR_AREA,
    LABEL_ZONE_TOP_RATIO,
    LABEL_ZONE_BOTTOM_RATIO,
    LABEL_EDGE_DENSITY_THRESH,
    LABEL_MIN_CONTOUR_AREA,
    LABEL_MIN_RECT_RATIO,
    OUTPUT_DIR,
)


# ─────────────────────────────────────────────────────────────
#  Classe principale
# ─────────────────────────────────────────────────────────────
class BottleDetector:
    """Détecte une bouteille, son bouchon et son étiquette."""

    def __init__(self, model_path: str | None = None, confidence: float | None = None):
        path = model_path or YOLO_MODEL_PATH
        self.confidence = confidence or YOLO_CONFIDENCE
        print(f"[Detector] Chargement modèle YOLO : {path}")
        self.model = YOLO(path)
        print("[Detector] Modèle chargé ✓")

    # ═════════════════════════════════════════════════════════
    #  API PUBLIQUE
    # ═════════════════════════════════════════════════════════
    def analyze(self, frame: np.ndarray, save: bool = True) -> dict[str, Any]:
        """
        Analyse une frame BGR.

        Retourne un dict :
        {
            "timestamp": "...",
            "bottle":    {"detected": bool, "confidence": float},
            "cap":       {"detected": bool, "confidence": float},
            "label":     {"detected": bool, "confidence": float},
            "status":    "OK" | "MISSING_BOTTLE" | "MISSING_CAP" | "MISSING_LABEL" | "INCOMPLETE",
            "image_path": "..." | null,
            "image_base64": "..." (JPEG base64, optionnel)
        }
        """
        t0 = time.time()
        annotated = frame.copy()
        result: dict[str, Any] = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bottle": {"detected": False, "confidence": 0.0},
            "cap": {"detected": False, "confidence": 0.0},
            "label": {"detected": False, "confidence": 0.0},
            "status": "MISSING_BOTTLE",
            "image_path": None,
        }

        # ── 1. Détection YOLO ──────────────────────────────
        detections = self.model(frame, conf=self.confidence, verbose=False)
        bottle_box = self._find_best_bottle(detections)

        if bottle_box is None:
            # Aucune bouteille détectée
            cv2.putText(
                annotated, "PAS DE BOUTEILLE", (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3,
            )
            result["status"] = "MISSING_BOTTLE"
        else:
            x1, y1, x2, y2, conf = bottle_box
            result["bottle"] = {"detected": True, "confidence": round(conf, 3)}

            # Rectangle bouteille
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                annotated, f"Bouteille {conf:.0%}", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2,
            )

            # ── 2. Bouchon ─────────────────────────────────
            cap_det, cap_conf, annotated = self._detect_cap(
                frame, annotated, x1, y1, x2, y2
            )
            result["cap"] = {"detected": cap_det, "confidence": round(cap_conf, 3)}

            # ── 3. Étiquette ───────────────────────────────
            label_det, label_conf, annotated = self._detect_label(
                frame, annotated, x1, y1, x2, y2
            )
            result["label"] = {"detected": label_det, "confidence": round(label_conf, 3)}

            # ── Statut global ──────────────────────────────
            missing = []
            if not cap_det:
                missing.append("CAP")
            if not label_det:
                missing.append("LABEL")

            if not missing:
                result["status"] = "OK"
            elif len(missing) == 2:
                result["status"] = "INCOMPLETE"
            else:
                result["status"] = f"MISSING_{missing[0]}"

            # Texte statut sur l'image
            status_color = (0, 200, 0) if result["status"] == "OK" else (0, 0, 255)
            cv2.putText(
                annotated, result["status"], (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.8, status_color, 4,
            )

        # ── Sauvegarde image ───────────────────────────────
        if save:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{ts}_{result['status']}.jpg"
            path = os.path.join(OUTPUT_DIR, fname)
            cv2.imwrite(path, annotated)
            result["image_path"] = path

        elapsed = time.time() - t0
        result["elapsed_ms"] = round(elapsed * 1000, 1)

        return result, annotated

    def analyze_to_json(self, frame: np.ndarray, include_image_base64: bool = False) -> str:
        """Retourne le résultat sous forme de chaîne JSON."""
        result, annotated = self.analyze(frame)
        if include_image_base64:
            _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            result["image_base64"] = base64.b64encode(buf).decode("utf-8")
        return json.dumps(result, ensure_ascii=False, indent=2)

    # ═════════════════════════════════════════════════════════
    #  MÉTHODES PRIVÉES
    # ═════════════════════════════════════════════════════════
    def _find_best_bottle(self, detections) -> tuple | None:
        """Trouve la meilleure détection « bottle » (plus haute confiance)."""
        best = None
        for r in detections:
            for box in r.boxes:
                cls_id = int(box.cls)
                cls_name = r.names[cls_id].lower()
                conf = float(box.conf)
                if cls_name == YOLO_BOTTLE_CLASS:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    if best is None or conf > best[4]:
                        best = (x1, y1, x2, y2, conf)
        return best

    # ── Détection bouchon ────────────────────────────────────
    def _detect_cap(
        self, frame, annotated, bx1, by1, bx2, by2
    ) -> tuple[bool, float, np.ndarray]:
        """
        Analyse la zone haute de la bouteille pour détecter un bouchon.
        Retourne (detected, confidence_score, annotated_frame).
        """
        h_bottle = by2 - by1
        cap_h = int(h_bottle * CAP_ZONE_RATIO)
        # Zone bouchon (au-dessus et dans le haut de la bouteille)
        cy1 = max(0, by1 - int(cap_h * 0.3))
        cy2 = by1 + cap_h
        cx1 = max(0, bx1 - 5)
        cx2 = min(frame.shape[1], bx2 + 5)

        zone = frame[cy1:cy2, cx1:cx2]
        if zone.size == 0:
            return False, 0.0, annotated

        gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Détection d'arêtes Canny
        edges = cv2.Canny(blur, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size

        # Contours significatifs
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        significant = [c for c in contours if cv2.contourArea(c) > CAP_MIN_CONTOUR_AREA]

        # Variance de couleur (bouchon = zone plus uniforme qu'air libre)
        color_var = float(np.var(gray))

        # Score composite
        score = 0.0
        if len(significant) >= 1:
            score += 0.35
        if edge_density > CAP_EDGE_DENSITY_THRESH:
            score += 0.35
        if color_var < CAP_COLOR_VAR_THRESH:
            score += 0.30

        detected = score >= 0.55

        # Annotation
        rect_color = (0, 220, 0) if detected else (0, 0, 255)
        cv2.rectangle(annotated, (cx1, cy1), (cx2, cy2), rect_color, 2)
        cap_text = "Bouchon OK" if detected else "Bouchon ABSENT"
        cv2.putText(
            annotated, cap_text, (cx1, cy1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, rect_color, 2,
        )

        return detected, round(score, 3), annotated

    # ── Détection étiquette ──────────────────────────────────
    def _detect_label(
        self, frame, annotated, bx1, by1, bx2, by2
    ) -> tuple[bool, float, np.ndarray]:
        """
        Analyse le corps de la bouteille pour détecter une étiquette.
        Retourne (detected, confidence_score, annotated_frame).
        """
        h_bottle = by2 - by1
        w_bottle = bx2 - bx1

        ly1 = by1 + int(h_bottle * LABEL_ZONE_TOP_RATIO)
        ly2 = by1 + int(h_bottle * LABEL_ZONE_BOTTOM_RATIO)
        lx1 = max(0, bx1 + int(w_bottle * 0.05))
        lx2 = min(frame.shape[1], bx2 - int(w_bottle * 0.05))

        zone = frame[ly1:ly2, lx1:lx2]
        if zone.size == 0:
            return False, 0.0, annotated

        gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)

        # Edges
        edges = cv2.Canny(blur, 30, 120)
        edge_density = np.count_nonzero(edges) / edges.size

        # Contours rectangulaires (étiquettes sont souvent rectangulaires)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        significant = [c for c in contours if cv2.contourArea(c) > LABEL_MIN_CONTOUR_AREA]

        # Chercher un grand rectangle (étiquette)
        has_rect = False
        for c in significant:
            x, y, w, h = cv2.boundingRect(c)
            if w > 0 and h > 0:
                aspect = min(w, h) / max(w, h)
                area_ratio = (w * h) / (zone.shape[0] * zone.shape[1])
                if aspect > LABEL_MIN_RECT_RATIO and area_ratio > 0.08:
                    has_rect = True
                    break

        # Analyse de texture — une étiquette a souvent du texte / motifs
        # On regarde la variance locale (Laplacien)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # Différence de couleur entre la zone étiquette et le reste de la bouteille
        # Une étiquette crée un contraste de couleur
        hsv_zone = cv2.cvtColor(zone, cv2.COLOR_BGR2HSV)
        sat_mean = float(np.mean(hsv_zone[:, :, 1]))  # Saturation moyenne

        # Score composite
        score = 0.0
        if edge_density > LABEL_EDGE_DENSITY_THRESH:
            score += 0.25
        if has_rect:
            score += 0.30
        if laplacian_var > 100:
            score += 0.25
        if sat_mean > 30 or len(significant) >= 3:
            score += 0.20

        detected = score >= 0.50

        # Annotation
        rect_color = (255, 165, 0) if detected else (0, 0, 255)
        cv2.rectangle(annotated, (lx1, ly1), (lx2, ly2), rect_color, 2)
        lbl_text = "Étiquette OK" if detected else "Étiquette ABSENTE"
        cv2.putText(
            annotated, lbl_text, (lx1, ly2 + 18),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, rect_color, 2,
        )

        return detected, round(score, 3), annotated
