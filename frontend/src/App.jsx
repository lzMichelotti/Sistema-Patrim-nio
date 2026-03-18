import { useCallback, useEffect, useState } from 'react';
import './App.css';

function App() {
  const [patrimonios, setPatrimonios] = useState([]);
  const [salas, setSalas] = useState([]);
  const [idEdicao, setIdEdicao] = useState(null);
  const [busca, setBusca] = useState('');
  const [mostrarEstatisticas, setMostrarEstatisticas] = useState(false);
  const [graficoKey, setGraficoKey] = useState(Date.now());
  const [erroGrafico, setErroGrafico] = useState(false);
  const [zoomGrafico, setZoomGrafico] = useState(1);
  
  const [form, setForm] = useState({
    numero_patrimonio_lamic: '',
    numero_patrimonio_ufsm: '',
    nome: '',
    sala_id: '',
    quantidade: 1,
    valor_total: 0
  });

  const API_URL = import.meta.env.VITE_API_URL || '/api';

  const carregarSalas = useCallback(() => {
    fetch(`${API_URL}/salas/`)
      .then(response => response.json())
      .then((data) => {
        const payload = Array.isArray(data) ? data : data?.salas;
        setSalas(Array.isArray(payload) ? payload : []);
      })
      .catch(() => setSalas([]));
  }, [API_URL]);

  const listarPatrimonios = useCallback(() => {
    fetch(`${API_URL}/patrimonios/`)
      .then(response => response.json())
      .then((data) => setPatrimonios(Array.isArray(data) ? data : []))
      .catch(() => setPatrimonios([]));
  }, [API_URL]);

  useEffect(() => {
    listarPatrimonios();
    carregarSalas();
  }, [listarPatrimonios, carregarSalas]);

  const formatCurrencyBR = (value) => {
    const numeric = Number(value) || 0;
    return numeric.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const getSalaNome = (sala) => {
    if (typeof sala === 'string') return sala;
    if (sala && typeof sala === 'object') return sala.nome || '';
    return '';
  };

  const getSalaId = (sala) => {
    if (typeof sala === 'number') return sala;
    if (typeof sala === 'string' && sala !== '') return Number(sala);
    if (sala && typeof sala === 'object' && sala.id != null) return Number(sala.id);
    return null;
  };

  const getSalaKey = (sala, index) => {
    if (typeof sala === 'string') return sala;
    if (sala && typeof sala === 'object') return sala.id ?? sala.nome ?? `sala-${index}`;
    return `sala-${index}`;
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
    const salaId = item.sala_id ?? getSalaId(item.sala) ?? '';
    setForm({
      numero_patrimonio_lamic: item.numero_patrimonio_lamic || '',
      numero_patrimonio_ufsm: item.numero_patrimonio_ufsm || '',
      nome: item.nome,
      sala_id: String(salaId),
      quantidade: item.quantidade,
      valor_total: item.valor_total
    });
    setIdEdicao(item.id);
  };

  const valorTextoOuNull = (valor) => {
    const texto = String(valor ?? '').trim();
    return texto === '' ? null : texto;
  };

  const montarPayload = () => ({
    numero_patrimonio_lamic: valorTextoOuNull(form.numero_patrimonio_lamic),
    numero_patrimonio_ufsm: valorTextoOuNull(form.numero_patrimonio_ufsm),
    nome: form.nome,
    quantidade: Number(form.quantidade) || 1,
    valor_total: Number(form.valor_total) || 0,
    sala_id: Number(form.sala_id),
  });

  const resetarForm = () => {
    setForm({
      numero_patrimonio_lamic: '',
      numero_patrimonio_ufsm: '',
      nome: '',
      sala_id: '',
      quantidade: 1,
      valor_total: 0,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.sala_id) {
      alert('Selecione uma sala.');
      return;
    }

    const payload = montarPayload();

    if (idEdicao) {
      fetch(`${API_URL}/patrimonios/${idEdicao}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(() => {
        listarPatrimonios();
        setIdEdicao(null);
        resetarForm();
      });
    } else {
      fetch(`${API_URL}/patrimonios/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(() => {
        listarPatrimonios();
        resetarForm();
      });
    }
  };

  const deletarItem = (id) => {
    if (confirm("Tem certeza?")) {
      fetch(`${API_URL}/patrimonios/${id}`, { method: 'DELETE' })
        .then(() => listarPatrimonios());
    }
  };

  const exportarPDF = () => {
    window.open(`${API_URL}/exportar_pdf`, '_blank');
  };

  const abrirEstatisticas = () => {
    if (!mostrarEstatisticas) {
      setGraficoKey(Date.now());
      setErroGrafico(false);
      setZoomGrafico(1);
    }
    setMostrarEstatisticas((prev) => !prev);
  };

  const fecharEstatisticas = () => {
    setMostrarEstatisticas(false);
  };

  const atualizarGrafico = () => {
    setGraficoKey(Date.now());
    setErroGrafico(false);
  };

  const aumentarZoom = () => {
    setZoomGrafico((zoomAtual) => Math.min(2.2, Number((zoomAtual + 0.15).toFixed(2))));
  };

  const diminuirZoom = () => {
    setZoomGrafico((zoomAtual) => Math.max(0.7, Number((zoomAtual - 0.15).toFixed(2))));
  };

  const resetarZoom = () => {
    setZoomGrafico(1);
  };

  useEffect(() => {
    if (!mostrarEstatisticas) {
      return undefined;
    }

    const overflowOriginal = document.body.style.overflow;
    const handleEsc = (event) => {
      if (event.key === 'Escape') {
        fecharEstatisticas();
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleEsc);

    return () => {
      document.body.style.overflow = overflowOriginal;
      window.removeEventListener('keydown', handleEsc);
    };
  }, [mostrarEstatisticas]);

  // Filtra a lista original baseado no que foi digitado
  const listaPatrimonios = Array.isArray(patrimonios) ? patrimonios : [];
  const listaSalas = Array.isArray(salas) ? salas : [];
  const normalizarTexto = (texto) =>
    (texto || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();

  const salasOcultasNoSelect = new Set(['laboratorio principal']);
  const listaSalasParaSelect = listaSalas.filter((sala) => {
    const nomeSala = getSalaNome(sala);
    return !salasOcultasNoSelect.has(normalizarTexto(nomeSala));
  });

  const getSalaNomeDoItem = (item) => {
    const nomeDireto = getSalaNome(item.sala);
    if (nomeDireto) return nomeDireto;

    const salaId = item.sala_id ?? getSalaId(item.sala);
    const salaEncontrada = listaSalas.find((sala) => Number(getSalaId(sala)) === Number(salaId));
    return getSalaNome(salaEncontrada) || '—';
  };

  const patrimoniosFiltrados = listaPatrimonios.filter((item) => {
    const salaNome = getSalaNomeDoItem(item);
    return (
      (item.nome || '').toLowerCase().includes(busca.toLowerCase()) ||
      (item.numero_patrimonio_lamic || '').includes(busca) ||
      salaNome.toLowerCase().includes(busca.toLowerCase())
    );
  });

  const graficoSrc = `${API_URL}/graficos/valor-por-sala?t=${graficoKey}`;

  return (
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
                  placeholder="Nº Patrimônio LAMIC (Opcional)"
                  value={form.numero_patrimonio_lamic}
                  onChange={handleChange}
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
                  name="sala_id"
                  value={form.sala_id}
                  onChange={handleChange}
                  required
                  className="input"
                >
                  <option value="">Selecione uma sala</option>
                  {listaSalasParaSelect.map((sala, index) => {
                    const salaNome = getSalaNome(sala);
                    const salaId = getSalaId(sala);
                    if (!salaNome) return null;

                    return (
                      <option key={getSalaKey(sala, index)} value={String(salaId ?? '')}>
                        {salaNome}
                      </option>
                    );
                  })}
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
                  {idEdicao ? '💾 Salvar Alterações' : 'Cadastrar'}
                </button>
                {idEdicao && (
                  <button
                    type="button"
                    onClick={() => { setIdEdicao(null); resetarForm(); }}
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
              <button onClick={exportarPDF} className="btn btn-danger btn-small">
                📄 PDF
              </button>
              <button onClick={abrirEstatisticas} className="btn btn-primary btn-small">
                {mostrarEstatisticas ? '📉 Fechar Estatísticas' : '📊 Estatísticas'}
              </button>
            </div>
          </div>

          <ul className="list">
            {patrimoniosFiltrados.map((item) => (
              <li key={item.id} className="list-item">
                <div className="item-info">
                  <p className="item-name">
                    <span style={{color: 'var(--primary-color)', fontWeight: '700'}}>{item.numero_patrimonio_lamic ? `#${item.numero_patrimonio_lamic}` : 'Sem LAMIC'}</span> - {item.nome}
                  </p>
                  <div className="item-details">
                    <span><strong>Sala:</strong> {getSalaNomeDoItem(item)}</span>
                    <span><strong>Quantidade:</strong> {item.quantidade}</span>
                    <span><strong>UFSM:</strong> {item.numero_patrimonio_ufsm || '—'}</span>
                  </div>
                </div>
                <div className="item-value">
                  {formatCurrencyBR(item.valor_total)}
                </div>
                <div className="item-actions">
                  <button onClick={() => prepararEdicao(item)} className="btn btn-primary btn-small">
                    ✏️
                  </button>
                  <button onClick={() => deletarItem(item.id)} className="btn btn-danger btn-small">
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

        {mostrarEstatisticas && (
          <div className="stats-modal-overlay" onClick={fecharEstatisticas}>
            <section
              className="stats-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="stats-modal-title"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="stats-modal-header">
                <h4 id="stats-modal-title">📈 Valor Total de Patrimônio por Sala</h4>
                <div className="stats-modal-actions">
                  <button onClick={atualizarGrafico} className="btn btn-secondary btn-small" type="button">
                    🔄 Atualizar
                  </button>
                  <button onClick={diminuirZoom} className="btn btn-secondary btn-small" type="button" aria-label="Diminuir zoom">
                    ➖
                  </button>
                  <button onClick={resetarZoom} className="btn btn-secondary btn-small" type="button" aria-label="Resetar zoom">
                    100%
                  </button>
                  <button onClick={aumentarZoom} className="btn btn-secondary btn-small" type="button" aria-label="Aumentar zoom">
                    ➕
                  </button>
                  <span className="zoom-label">Zoom: {Math.round(zoomGrafico * 100)}%</span>
                  <button onClick={fecharEstatisticas} className="btn btn-primary btn-small" type="button">
                    ✖ Fechar
                  </button>
                </div>
              </div>

              {erroGrafico ? (
                <p className="stats-error">Não foi possível carregar o gráfico agora.</p>
              ) : (
                <div className="stats-image-viewport">
                  <img
                    src={graficoSrc}
                    alt="Gráfico de valor total por sala"
                    className="stats-image"
                    style={{ width: `${zoomGrafico * 100}%`, maxWidth: 'none' }}
                    onError={() => setErroGrafico(true)}
                  />
                </div>
              )}
            </section>
          </div>
        )}
        
        <footer className="footer">
          <p>Desenvolvido por Lorenzo Michelotti Palma</p>
        </footer>
      </div>

  );
}

export default App; 