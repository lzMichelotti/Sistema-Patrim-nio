import { useState, useEffect } from 'react';
import './App.css';
import ChatWidget from './components/ChatWidget';

function App() {
  const [patrimonios, setPatrimonios] = useState([]);
  const [idEdicao, setIdEdicao] = useState(null);
  const [busca, setBusca] = useState('');
  
  const [form, setForm] = useState({
    numero_patrimonio: '',
    nome: '',
    sala: '',
    quantidade: 1,
    valor: 0
  });

  useEffect(() => {
    listarPatrimonios();
  }, []);

  const listarPatrimonios = () => {
    fetch('http://127.0.0.1:8000/patrimonios/')
      .then(response => response.json())
      .then(data => setPatrimonios(data));
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const prepararEdicao = (item) => {
    setForm({
      numero_patrimonio: item.numero_patrimonio,
      nome: item.nome,
      sala: item.sala,
      quantidade: item.quantidade,
      valor: item.valor
    });
    setIdEdicao(item.id);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (idEdicao) {
      fetch(`http://127.0.0.1:8000/patrimonios/${idEdicao}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }).then(() => {
        listarPatrimonios();
        setIdEdicao(null);
        setForm({ numero_patrimonio: '', nome: '', sala: '', quantidade: 1, valor: 0 });
      });
    } else {
      fetch('http://127.0.0.1:8000/patrimonios/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      }).then(() => {
        listarPatrimonios();
        setForm({ numero_patrimonio: '', nome: '', sala: '', quantidade: 1, valor: 0 });
      });
    }
  };

  const deletarItem = (id) => {
    if (confirm("Tem certeza?")) {
      fetch(`http://127.0.0.1:8000/patrimonios/${id}`, { method: 'DELETE' })
        .then(() => listarPatrimonios());
    }
  };

  const exportarExcel = () => {
    window.open('http://127.0.0.1:8000/exportar_excel', '_blank');
  };

  const exportarPDF = () => {
    window.open('http://127.0.0.1:8000/exportar_pdf', '_blank');
  };

  // Filtra a lista original baseado no que foi digitado
  const patrimoniosFiltrados = patrimonios.filter((item) =>
    item.nome.toLowerCase().includes(busca.toLowerCase()) ||
    item.numero_patrimonio.includes(busca) ||
    item.sala.toLowerCase().includes(busca.toLowerCase())
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
      <h1 className="app-title">Sistema de Patrimônio - LAMIC</h1>

      <div className="form-container">
        <h3>{idEdicao ? 'Editar Patrimônio' : 'Novo Patrimônio'}</h3>
        <form onSubmit={handleSubmit} className="form">
          <input
            name="numero_patrimonio"
            placeholder="Nº Patrimônio"
            value={form.numero_patrimonio}
            onChange={handleChange}
            required
            className="input"
          />
          <input
            name="nome"
            placeholder="Nome"
            value={form.nome}
            onChange={handleChange}
            required
            className="input"
          />
          <div className="input-grid">
            <input
              name="sala"
              placeholder="Sala"
              value={form.sala}
              onChange={handleChange}
              required
              className="input"
            />
            <input
              type="number"
              name="quantidade"
              placeholder="Qtd"
              value={form.quantidade}
              onChange={handleChange}
              className="input"
            />
            <input
              type="number"
              name="valor"
              placeholder="Valor"
              value={form.valor}
              onChange={handleChange}
              className="input"
            />
          </div>
          <button
            type="submit"
            className={`btn ${idEdicao ? 'btn-warning' : 'btn-success'}`}
          >
            {idEdicao ? 'Salvar Alterações' : 'Cadastrar'}
          </button>
          {idEdicao && (
            <button
              type="button"
              onClick={() => { setIdEdicao(null); setForm({ numero_patrimonio: '', nome: '', sala: '', quantidade: 1, valor: 0 }); }}
              className="btn btn-secondary"
            >
              Cancelar
            </button>
          )}
        </form>
      </div>

      <div className="header">
        <h3>Lista de Ativos ({patrimoniosFiltrados.length})</h3>

        <div className="button-group">
          <button onClick={exportarExcel} className="btn btn-success">
            📊 Exportar Excel
          </button>
          <button onClick={exportarPDF} className="btn btn-danger">
            📄 PDF
          </button>
          <input
            type="text"
            placeholder="Buscar..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      <ul className="list">
        {patrimoniosFiltrados.map((item) => (
          <li key={item.id} className="list-item">
            <div>
              <strong>{item.numero_patrimonio}</strong> - {item.nome}
              <div className="item-details">
                Sala: {item.sala} | Qtd: {item.quantidade}
              </div>
            </div>
            <div className="item-actions">
              <div className="item-value">R$ {item.valor}</div>
              <button onClick={() => prepararEdicao(item)} className="btn btn-primary">
                Editar
              </button>
              <button onClick={() => deletarItem(item.id)} className="btn btn-danger">
                X
              </button>
            </div>
          </li>
        ))}
        {patrimoniosFiltrados.length === 0 && (
          <p className="no-items">Nenhum item encontrado.</p>
        )}
      </ul>
    </div>
    
    {/* --- CORREÇÃO 2: Passamos a função correta para o Widget --- */}
    <ChatWidget onNewItem={handleNovoItemIA} />
    </>
  );
}

export default App; 