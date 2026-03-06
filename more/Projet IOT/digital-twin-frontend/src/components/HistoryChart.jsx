import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { getHistory } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function HistoryChart({ measurement }) {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getHistory(measurement, '-1h');

        const labels = response.data.map(item =>
          new Date(item._time).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
          })
        );

        const values = response.data.map(item => item._value);

        setChartData({
          labels,
          datasets: [
            {
              label: measurement === 'ultrason' ? 'Distance (cm)' : 'Valeur',
              data: values,
              borderColor: '#4f46e5',
              backgroundColor: 'rgba(79, 70, 229, 0.1)',
              fill: true,
              tension: 0.4
            }
          ]
        });
        setLoading(false);
      } catch (error) {
        console.error('Erreur chargement historique:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh toutes les 30s

    return () => clearInterval(interval);
  }, [measurement]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        ticks: {
          color: '#8b92b0'
        }
      },
      x: {
        grid: {
          display: false
        },
        ticks: {
          color: '#8b92b0',
          maxTicksLimit: 10
        }
      }
    }
  };

  if (loading) {
    return <div>Chargement...</div>;
  }

  if (!chartData) {
    return <div>Aucune donnée disponible</div>;
  }

  return (
    <div style={{ height: '200px', width: '100%' }}>
      <Line data={chartData} options={options} />
    </div>
  );
}
