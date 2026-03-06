import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Grid, Text } from '@react-three/drei';
import { Suspense } from 'react';

function Conveyor({ motorRunning }) {
  return (
    <group position={[0, 0, 0]}>
      {/* Base du convoyeur */}
      <mesh position={[0, -0.5, 0]}>
        <boxGeometry args={[8, 0.1, 2]} />
        <meshStandardMaterial color="#4a5568" />
      </mesh>

      {/* Bandes du convoyeur */}
      <mesh position={[0, -0.4, 0.9]}>
        <boxGeometry args={[8, 0.05, 0.1]} />
        <meshStandardMaterial color={motorRunning ? '#3b82f6' : '#6b7280'} />
      </mesh>
      <mesh position={[0, -0.4, -0.9]}>
        <boxGeometry args={[8, 0.05, 0.1]} />
        <meshStandardMaterial color={motorRunning ? '#3b82f6' : '#6b7280'} />
      </mesh>

      {/* Supports */}
      {[-3, -1, 1, 3].map((x) => (
        <mesh key={x} position={[x, -1, 0]}>
          <cylinderGeometry args={[0.1, 0.1, 1]} />
          <meshStandardMaterial color="#2d3748" />
        </mesh>
      ))}
    </group>
  );
}

function Bottle({ detected, position = [0, 0, 0] }) {
  if (!detected) return null;

  return (
    <group position={position}>
      {/* Corps de la bouteille */}
      <mesh position={[0, 0.5, 0]}>
        <cylinderGeometry args={[0.15, 0.2, 1, 16]} />
        <meshStandardMaterial
          color="#60a5fa"
          transparent
          opacity={0.7}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>

      {/* Bouchon */}
      <mesh position={[0, 1.1, 0]}>
        <cylinderGeometry args={[0.12, 0.12, 0.2, 16]} />
        <meshStandardMaterial color="#10b981" />
      </mesh>

      {/* Liquide */}
      <mesh position={[0, 0.3, 0]}>
        <cylinderGeometry args={[0.14, 0.18, 0.6, 16]} />
        <meshStandardMaterial
          color="#fbbf24"
          transparent
          opacity={0.6}
        />
      </mesh>
    </group>
  );
}

function Camera3DModel({ position }) {
  return (
    <group position={position}>
      {/* Corps caméra */}
      <mesh>
        <boxGeometry args={[0.3, 0.2, 0.4]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>

      {/* Lentille */}
      <mesh position={[0, 0, 0.25]}>
        <cylinderGeometry args={[0.08, 0.08, 0.1, 16]} rotation={[Math.PI / 2, 0, 0]} />
        <meshStandardMaterial color="#374151" metalness={0.8} />
      </mesh>

      {/* Support */}
      <mesh position={[0, 0.3, 0]}>
        <cylinderGeometry args={[0.05, 0.05, 0.4]} />
        <meshStandardMaterial color="#4b5563" />
      </mesh>
    </group>
  );
}

function LEDs({ leds }) {
  return (
    <group position={[4, 1, 0]}>
      {/* LED Verte */}
      <mesh position={[0, 0.5, 0]}>
        <sphereGeometry args={[0.15, 16, 16]} />
        <meshStandardMaterial
          color="#10b981"
          emissive={leds?.verte ? '#10b981' : '#000000'}
          emissiveIntensity={leds?.verte ? 2 : 0}
        />
      </mesh>

      {/* LED Orange */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[0.15, 16, 16]} />
        <meshStandardMaterial
          color="#f59e0b"
          emissive={leds?.orange ? '#f59e0b' : '#000000'}
          emissiveIntensity={leds?.orange ? 2 : 0}
        />
      </mesh>

      {/* LED Rouge */}
      <mesh position={[0, -0.5, 0]}>
        <sphereGeometry args={[0.15, 16, 16]} />
        <meshStandardMaterial
          color="#ef4444"
          emissive={leds?.rouge ? '#ef4444' : '#000000'}
          emissiveIntensity={leds?.rouge ? 2 : 0}
        />
      </mesh>

      {/* Support */}
      <mesh position={[0, 0, -0.3]}>
        <boxGeometry args={[0.4, 1.2, 0.1]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>
    </group>
  );
}

function Sensor({ position, label, active }) {
  return (
    <group position={position}>
      {/* Corps capteur */}
      <mesh>
        <boxGeometry args={[0.2, 0.2, 0.3]} />
        <meshStandardMaterial
          color={active ? '#3b82f6' : '#6b7280'}
          emissive={active ? '#3b82f6' : '#000000'}
          emissiveIntensity={active ? 0.5 : 0}
        />
      </mesh>

      {/* Label */}
      <Text
        position={[0, 0.3, 0]}
        fontSize={0.15}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
    </group>
  );
}

function Scene({ systemState }) {
  const bottleDetected = systemState?.ultrason?.flacon_detecte || false;
  const motorRunning = systemState?.moteur?.etat === 'ON';
  const leds = systemState?.leds;

  return (
    <>
      {/* Éclairage */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
      <pointLight position={[-10, 10, -5]} intensity={0.5} />

      {/* Grille */}
      <Grid
        args={[20, 20]}
        cellSize={0.5}
        cellThickness={0.5}
        cellColor="#374151"
        sectionSize={2}
        sectionThickness={1}
        sectionColor="#4b5563"
        fadeDistance={30}
        fadeStrength={1}
        followCamera={false}
      />

      {/* Convoyeur */}
      <Conveyor motorRunning={motorRunning} />

      {/* Bouteille */}
      <Bottle detected={bottleDetected} position={[0, 0, 0]} />

      {/* Caméra */}
      <Camera3DModel position={[0, 2.5, 0]} />

      {/* LEDs */}
      <LEDs leds={leds} />

      {/* Capteur ultrason */}
      <Sensor
        position={[-3, 0.5, 1.5]}
        label="Ultrason"
        active={bottleDetected}
      />

      {/* Capteur de poids */}
      <Sensor
        position={[2, -0.3, 1.5]}
        label="Poids"
        active={systemState?.poids?.valeur_g > 0}
      />

      {/* Titre */}
      <Text
        position={[0, 4, -2]}
        fontSize={0.5}
        color="#4f46e5"
        anchorX="center"
        anchorY="middle"
        font="/fonts/Inter-Bold.ttf"
      >
        Système IoT - Vue 3D
      </Text>

      {/* Contrôles caméra */}
      <OrbitControls
        makeDefault
        minPolarAngle={0}
        maxPolarAngle={Math.PI / 2}
        enableDamping
        dampingFactor={0.05}
      />

      <PerspectiveCamera makeDefault position={[8, 6, 8]} fov={50} />
    </>
  );
}

export default function Scene3D({ systemState }) {
  return (
    <div style={{ width: '100%', height: 'calc(100vh - 80px)', background: '#0a0e1a' }}>
      <Canvas shadows>
        <Suspense fallback={null}>
          <Scene systemState={systemState} />
        </Suspense>
      </Canvas>

      {/* Infos */}
      <div style={{
        position: 'absolute',
        bottom: '2rem',
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(0, 0, 0, 0.7)',
        padding: '1rem 2rem',
        borderRadius: '12px',
        color: 'white',
        fontSize: '0.875rem',
        textAlign: 'center'
      }}>
        <p style={{ margin: 0 }}>
          🖱️ Clic gauche + glisser pour tourner | 🖱️ Molette pour zoomer | 🖱️ Clic droit + glisser pour déplacer
        </p>
      </div>
    </div>
  );
}
