import { useState } from 'react'
import './App.css'

interface AnalysisResult {
  relatorio: string;
  feedback_llm: string;
  violacoes: string[];
  alertas: string[];
}

function App() {
  const [preco, setPreco] = useState<string>("");
  const [cac, setCac] = useState<string>("");
  const [rpc, setRpc] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/analisar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          preco: parseFloat(preco),
          cac: parseFloat(cac),
          rpc: parseFloat(rpc)
        }),
      });

      if (!response.ok) {
        throw new Error('Falha na requisição');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Erro:", error);
      alert("Erro ao conectar com a API. Verifique se o backend está rodando.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Validador de Precificação</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Preço Mensal (R$)</label>
            <input
              type="number"
              placeholder="Ex: 99.00"
              value={preco}
              onChange={(e) => setPreco(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Custo de Aquisição (CAC) (R$)</label>
            <input
              type="number"
              placeholder="Ex: 100.00"
              value={cac}
              onChange={(e) => setCac(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Renda Per Capita (RPC) (R$)</label>
            <input
              type="number"
              placeholder="Ex: 3800.00"
              value={rpc}
              onChange={(e) => setRpc(e.target.value)}
              required
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Analisando...' : 'Analisar Estratégia'}
          </button>
        </form>
      </div>

      {result && (
        <div className="results">
          <div className="feedback-section">
            <h2>🤖 Feedback do Consultor IA</h2>
            <div className="markdown-body">

              {result.feedback_llm.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </div>

          <div className="technical-section">
            <h3>Relatório Técnico</h3>
            <pre>{result.relatorio}</pre>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
