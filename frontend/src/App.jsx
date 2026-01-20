import { useState, useEffect } from 'react';
import './App.css';
import ChatWidget from './components/ChatWidget';

function App() {
  const [patrimonios, setPatrimonios] = useState([]);
  const [salas, setSalas] = useState([]);
  const [idEdicao, setIdEdicao] = useState(null);
  const [busca, setBusca] = useState('');
  
  const [form, setForm] = useState({
    numero_patrimonio_lamic: '',
    numero_patrimonio_ufsm: '',
    nome: '',
    sala: '',
    quantidade: 1,
    valor_total: 0
  });

  const API_URL = import.meta.env.VITE_API_URL || '/api';

  useEffect(() => {
    listarPatrimonios();
    carregarSalas();
  }, []);

  const carregarSalas = () => {
    fetch(`${API_URL}/salas/`)
      .then(response => response.json())
      .then(data => setSalas(data.salas));
  };

  const listarPatrimonios = () => {
    fetch(`${API_URL}/patrimonios/`)
      .then(response => response.json())
      .then(data => setPatrimonios(data));
  };

  const formatCurrencyBR = (value) => {
    const numeric = Number(value) || 0;
    return numeric.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const handleValorChange = (e) => {
    const digits = e.target.value.replace(/\D/g, '');
    const numeric = digits ? Number(digits) / 100 : 0;
    setForm((prev) => ({ ...prev, valor_total: numeric }));
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const prepararEdicao = (item) => {
    setForm({
      numero_patrimonio_lamic: item.numero_patrimonio_lamic || '',
      numero_patrimonio_ufsm: item.numero_patrimonio_ufsm || '',
      nome: item.nome,
      sala: item.sala,
      quantidade: item.quantidade,
      valor_total: item.valor_total
    });
    setIdEdicao(item.id);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (idEdicao) {
      const salaPath = encodeURIComponent(form.sala);
      fetch(`${API_URL}/patrimonios/${salaPath}/${idEdicao}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }).then(() => {
        listarPatrimonios();
        setIdEdicao(null);
        setForm({ numero_patrimonio_lamic: '', numero_patrimonio_ufsm: '', nome: '', sala: '', quantidade: 1, valor_total: 0 });
      });
    } else {
      fetch(`${API_URL}/patrimonios/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }).then(() => {
        listarPatrimonios();
        setForm({ numero_patrimonio_lamic: '', numero_patrimonio_ufsm: '', nome: '', sala: '', quantidade: 1, valor_total: 0 });
      });
    }
  };

  const deletarItem = (sala, id) => {
    if (confirm("Tem certeza?")) {
      const salaPath = encodeURIComponent(sala);
      fetch(`${API_URL}/patrimonios/${salaPath}/${id}`, { method: 'DELETE' })
        .then(() => listarPatrimonios());
    }
  };

  const exportarExcel = () => {
    window.open(`${API_URL}/exportar_excel`, '_blank');
  };

  const exportarPDF = () => {
    window.open(`${API_URL}/exportar_pdf`, '_blank');
  };

  // Filtra a lista original baseado no que foi digitado
  const patrimoniosFiltrados = patrimonios.filter((item) =>
    (item.nome || '').toLowerCase().includes(busca.toLowerCase()) ||
    (item.numero_patrimonio_lamic || '').includes(busca) ||
    (item.sala || '').toLowerCase().includes(busca.toLowerCase())
  );

  // --- CORREÇÃO 1: NOVA FUNÇÃO SIMPLES ---
  // Essa função apenas recebe o dado que JÁ FOI SALVO pelo Python e atualiza a tela
  const handleNovoItemIA = (itemJaSalvo) => {
    // Opção A: Adiciona direto no estado (mais rápido, "instantâneo")
    setPatrimonios((prev) => [...prev, itemJaSalvo]);
    
    // Opção B: Se preferir garantir 100%, pode chamar listarPatrimonios() aqui também
    // listarPatrimonios(); 
  };

  return (
    <>
      <div className="app-container">
        <header className="hero-header">
          <div className="hero-content">
            <img
              src="/logo_lamic.png"
              alt="LAMIC"
              className="logo-img"
            />
            <div className="hero-title">
              <h1 className="header-title">Sistema de Patrimônio</h1>
              <p className="header-subtitle">LAMIC - Laboratório de Análises Micotoxicológicas - UFSM</p>
            </div>
            <img
              src="/ufsm_png.png"
              alt="UFSM"
              className="logo-img"
            />
          </div>
        </header>

        <div className="app-main">
          <div className="form-container">
            <h3>{idEdicao ? '✏️ Editar Patrimônio' : '➕ Novo Patrimônio'}</h3>
            <form onSubmit={handleSubmit} className="form">
              <div className="input-grid">
                <input
                  name="numero_patrimonio_lamic"
                  placeholder="Nº Patrimônio LAMIC"
                  value={form.numero_patrimonio_lamic}
                  onChange={handleChange}
                  required
                  className="input"
                />
                <input
                  name="numero_patrimonio_ufsm"
                  placeholder="Nº Patrimônio UFSM (Opcional)"
                  value={form.numero_patrimonio_ufsm}
                  onChange={handleChange}
                  className="input"
                />
                <input
                  name="nome"
                  placeholder="Nome do Ativo"
                  value={form.nome}
                  onChange={handleChange}
                  required
                  className="input"
                />
              </div>
              <div className="input-grid">
                <select
                  name="sala"
                  value={form.sala}
                  onChange={handleChange}
                  required
                  className="input"
                >
                  <option value="">Selecione uma sala</option>
                  {salas.map((sala) => (
                    <option key={sala} value={sala}>
                      {sala}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  name="quantidade"
                  placeholder="Quantidade"
                  value={form.quantidade}
                  onChange={handleChange}
                  className="input"
                />
                <input
                  name="valor_total"
                  placeholder="Valor Total (R$)"
                  value={formatCurrencyBR(form.valor_total)}
                  onChange={handleValorChange}
                  inputMode="numeric"
                  className="input"
                />
              </div>
              <div className="button-group">
                <button
                  type="submit"
                  className={`btn ${idEdicao ? 'btn-warning' : 'btn-success'}`}
                >
                  {idEdicao ? '💾 Salvar Alterações' : '✅ Cadastrar'}
                </button>
                {idEdicao && (
                  <button
                    type="button"
                    onClick={() => { setIdEdicao(null); setForm({ numero_patrimonio_lamic: '', numero_patrimonio_ufsm: '', nome: '', sala: '', quantidade: 1, valor_total: 0 }); }}
                    className="btn btn-secondary"
                  >
                    ❌ Cancelar
                  </button>
                )}
              </div>
            </form>
          </div>

          <div className="section-header">
            <h3>📋 Lista de Ativos ({patrimoniosFiltrados.length})</h3>
            <div className="button-group">
              <input
                type="text"
                placeholder="🔍 Buscar por nome, sala ou número..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="search-input"
              />
              <button onClick={exportarExcel} className="btn btn-success btn-small">
                📊 Excel
              </button>
              <button onClick={exportarPDF} className="btn btn-danger btn-small">
                📄 PDF
              </button>
            </div>
          </div>

          <ul className="list">
            {patrimoniosFiltrados.map((item) => (
              <li key={item.id} className="list-item">
                <div className="item-info">
                  <p className="item-name">
                    <span style={{color: 'var(--primary-color)', fontWeight: '700'}}>#{item.numero_patrimonio_lamic}</span> - {item.nome}
                  </p>
                  <div className="item-details">
                    <span><strong>Sala:</strong> {item.sala}</span>
                    <span><strong>Quantidade:</strong> {item.quantidade}</span>
                    <span><strong>UFSM:</strong> {item.numero_patrimonio_ufsm || '—'}</span>
                  </div>
                </div>
                <div className="item-value">
                  R$ {parseFloat(item.valor_total).toFixed(2)}
                </div>
                <div className="item-actions">
                  <button onClick={() => prepararEdicao(item)} className="btn btn-primary btn-small">
                    ✏️
                  </button>
                  <button onClick={() => deletarItem(item.sala, item.id)} className="btn btn-danger btn-small">
                    🗑️
                  </button>
                </div>
              </li>
            ))}
            {patrimoniosFiltrados.length === 0 && (
              <div style={{textAlign: 'center', padding: '40px', color: 'rgba(255,255,255,0.6)'}}>
                <p style={{fontSize: '1.1em'}}>📭 Nenhum item encontrado</p>
                <p style={{fontSize: '0.9em'}}>Cadastre o primeiro patrimônio usando o formulário acima</p>
              </div>
            )}
          </ul>
        </div>
        
        <footer className="footer">
          <p>Desenvolvido por Lorenzo Michelotti Palma</p>
        </footer>
      </div>

      <ChatWidget onNewItem={handleNovoItemIA} />
    </>
  );
}

export default App; 