import { useCallback, useEffect, useState } from 'react';
import './App.css';

const COMPONENTE_VAZIO = { nome: '', numero_serie: '', quantidade: 1, valor: 0, observacao: '' };

function App() {
  const [patrimonios, setPatrimonios] = useState([]);
  const [salas, setSalas] = useState([]);
  const [idEdicao, setIdEdicao] = useState(null);
  const [mostrarModal, setMostrarModal] = useState(false);
  const [mostrarEstatisticas, setMostrarEstatisticas] = useState(false);
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [expandidos, setExpandidos] = useState(new Set());
  const [modalComponente, setModalComponente] = useState(null); // { patrimonioId, componente: null|obj }
  const [componenteForm, setComponenteForm] = useState(COMPONENTE_VAZIO);

  const [filtros, setFiltros] = useState({
    nome: '',
    numero_patrimonio_lamic: '',
    numero_patrimonio_ufsm: '',
    sala_id: '',
    valor_min: '',
    valor_max: '',
    quantidade_min: '',
    quantidade_max: '',
  });
  const [graficoKey, setGraficoKey] = useState(Date.now());
  const [erroGrafico, setErroGrafico] = useState(false);
  const [zoomGrafico, setZoomGrafico] = useState(1);
  const [abaAtual, setAbaAtual] = useState('ativos');

  const [form, setForm] = useState({
    numero_patrimonio_lamic: '',
    numero_patrimonio_ufsm: '',
    nome: '',
    sala_id: '',
    quantidade: 1,
    valor_total: 0,
    ativo: true,
  });

  const API_URL = import.meta.env.VITE_API_URL || '/api';

  const carregarSalas = useCallback(() => {
    fetch(`${API_URL}/salas/`)
      .then((r) => r.json())
      .then((data) => {
        const payload = Array.isArray(data) ? data : data?.salas;
        setSalas(Array.isArray(payload) ? payload : []);
      })
      .catch(() => setSalas([]));
  }, [API_URL]);

  const listarPatrimonios = useCallback(() => {
    fetch(`${API_URL}/patrimonios/`)
      .then((r) => r.json())
      .then((data) => setPatrimonios(Array.isArray(data) ? data : []))
      .catch(() => setPatrimonios([]));
  }, [API_URL]);

  useEffect(() => {
    listarPatrimonios();
    carregarSalas();
  }, [listarPatrimonios, carregarSalas]);

  const formatCurrencyBR = (value) => {
    const numeric = Number(value) || 0;
    return numeric.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 });
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

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const resetarForm = () => setForm({ numero_patrimonio_lamic: '', numero_patrimonio_ufsm: '', nome: '', sala_id: '', quantidade: 1, valor_total: 0, ativo: true });

  const abrirModalCadastro = () => { setIdEdicao(null); resetarForm(); setMostrarModal(true); };
  const fecharModal = () => { setMostrarModal(false); setIdEdicao(null); resetarForm(); };

  const prepararEdicao = (item) => {
    const salaId = item.sala_id ?? getSalaId(item.sala) ?? '';
    setForm({
      numero_patrimonio_lamic: item.numero_patrimonio_lamic || '',
      numero_patrimonio_ufsm: item.numero_patrimonio_ufsm || '',
      nome: item.nome,
      sala_id: String(salaId),
      quantidade: item.quantidade,
      valor_total: item.valor_total,
      ativo: item.ativo !== false,
    });
    setIdEdicao(item.id);
    setMostrarModal(true);
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
    ativo: form.ativo,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.sala_id) { alert('Selecione uma sala.'); return; }
    const payload = montarPayload();
    const url = idEdicao ? `${API_URL}/patrimonios/${idEdicao}` : `${API_URL}/patrimonios/`;
    const method = idEdicao ? 'PUT' : 'POST';
    fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      .then(() => { listarPatrimonios(); fecharModal(); });
  };

  const deletarItem = (id) => {
    if (confirm('Tem certeza?')) {
      fetch(`${API_URL}/patrimonios/${id}`, { method: 'DELETE' }).then(() => listarPatrimonios());
    }
  };

  // Componentes
  const toggleExpandido = (id) => {
    setExpandidos((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const abrirModalComponente = (patrimonioId, componente = null) => {
    setModalComponente({ patrimonioId, componente });
    setComponenteForm(componente
      ? { nome: componente.nome, numero_serie: componente.numero_serie || '', quantidade: componente.quantidade, valor: componente.valor || 0, observacao: componente.observacao || '' }
      : COMPONENTE_VAZIO
    );
  };

  const fecharModalComponente = () => { setModalComponente(null); setComponenteForm(COMPONENTE_VAZIO); };

  const handleValorComponenteChange = (e) => {
    const digits = e.target.value.replace(/\D/g, '');
    const numeric = digits ? Number(digits) / 100 : 0;
    setComponenteForm((prev) => ({ ...prev, valor: numeric }));
  };

  const handleSubmitComponente = (e) => {
    e.preventDefault();
    const { patrimonioId, componente } = modalComponente;
    const payload = {
      nome: componenteForm.nome,
      numero_serie: componenteForm.numero_serie || null,
      quantidade: Number(componenteForm.quantidade) || 1,
      valor: Number(componenteForm.valor) || 0,
      observacao: componenteForm.observacao || null,
    };
    const url = componente ? `${API_URL}/componentes/${componente.id}` : `${API_URL}/patrimonios/${patrimonioId}/componentes/`;
    const method = componente ? 'PUT' : 'POST';
    fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      .then(() => { listarPatrimonios(); fecharModalComponente(); });
  };

  const deletarComponente = (id) => {
    if (confirm('Remover este componente?')) {
      fetch(`${API_URL}/componentes/${id}`, { method: 'DELETE' }).then(() => listarPatrimonios());
    }
  };

  // Estatísticas
  const exportarPDF = () => window.open(`${API_URL}/exportar_pdf`, '_blank');
  const abrirEstatisticas = () => { if (!mostrarEstatisticas) { setGraficoKey(Date.now()); setErroGrafico(false); setZoomGrafico(1); } setMostrarEstatisticas((p) => !p); };
  const fecharEstatisticas = () => setMostrarEstatisticas(false);
  const atualizarGrafico = () => { setGraficoKey(Date.now()); setErroGrafico(false); };
  const aumentarZoom = () => setZoomGrafico((z) => Math.min(2.2, Number((z + 0.15).toFixed(2))));
  const diminuirZoom = () => setZoomGrafico((z) => Math.max(0.7, Number((z - 0.15).toFixed(2))));
  const resetarZoom = () => setZoomGrafico(1);

  const algumModalAberto = mostrarModal || mostrarEstatisticas || !!modalComponente;
  useEffect(() => {
    if (!algumModalAberto) return undefined;
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const handleEsc = (e) => {
      if (e.key !== 'Escape') return;
      if (modalComponente) fecharModalComponente();
      else if (mostrarModal) fecharModal();
      else if (mostrarEstatisticas) fecharEstatisticas();
    };
    window.addEventListener('keydown', handleEsc);
    return () => { document.body.style.overflow = original; window.removeEventListener('keydown', handleEsc); };
  }, [algumModalAberto, modalComponente, mostrarModal, mostrarEstatisticas]);

  // Dados derivados
  const listaPatrimonios = Array.isArray(patrimonios) ? patrimonios : [];
  const listaSalas = Array.isArray(salas) ? salas : [];

  const normalizarTexto = (texto) =>
    (texto || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

  const salasOcultasNoSelect = new Set(['laboratorio principal']);
  const listaSalasParaSelect = listaSalas.filter(
    (sala) => !salasOcultasNoSelect.has(normalizarTexto(getSalaNome(sala)))
  );

  const getSalaNomeDoItem = (item) => {
    const nomeDireto = getSalaNome(item.sala);
    if (nomeDireto) return nomeDireto;
    const salaId = item.sala_id ?? getSalaId(item.sala);
    const found = listaSalas.find((s) => Number(getSalaId(s)) === Number(salaId));
    return getSalaNome(found) || '—';
  };

  const setFiltro = (campo, valor) => setFiltros((prev) => ({ ...prev, [campo]: valor }));
  const limparFiltros = () => setFiltros({ nome: '', numero_patrimonio_lamic: '', numero_patrimonio_ufsm: '', sala_id: '', valor_min: '', valor_max: '', quantidade_min: '', quantidade_max: '' });
  const filtrosAtivos = Object.values(filtros).filter((v) => v !== '').length;

  const patrimoniosFiltrados = listaPatrimonios.filter((item) => {
    const isAtivo = item.ativo !== false;
    if (abaAtual === 'ativos' && !isAtivo) return false;
    if (abaAtual === 'inativos' && isAtivo) return false;
    if (filtros.nome && !normalizarTexto(item.nome).includes(normalizarTexto(filtros.nome))) return false;
    if (filtros.numero_patrimonio_lamic && !(item.numero_patrimonio_lamic || '').toLowerCase().includes(filtros.numero_patrimonio_lamic.toLowerCase())) return false;
    if (filtros.numero_patrimonio_ufsm && !(item.numero_patrimonio_ufsm || '').toLowerCase().includes(filtros.numero_patrimonio_ufsm.toLowerCase())) return false;
    if (filtros.sala_id) {
      const itemSalaId = item.sala_id ?? getSalaId(item.sala);
      if (String(itemSalaId) !== filtros.sala_id) return false;
    }
    if (filtros.valor_min !== '' && Number(item.valor_total) < Number(filtros.valor_min)) return false;
    if (filtros.valor_max !== '' && Number(item.valor_total) > Number(filtros.valor_max)) return false;
    if (filtros.quantidade_min !== '' && Number(item.quantidade) < Number(filtros.quantidade_min)) return false;
    if (filtros.quantidade_max !== '' && Number(item.quantidade) > Number(filtros.quantidade_max)) return false;
    return true;
  });

  const ordenarPorLamic = (a, b) => {
    const cA = a.numero_patrimonio_lamic || '';
    const cB = b.numero_patrimonio_lamic || '';
    if (cA && !cB) return -1;
    if (!cA && cB) return 1;
    return cA.localeCompare(cB, 'pt-BR', { numeric: true });
  };

  const itensAgrupados = (() => {
    const grupos = {};
    for (const item of patrimoniosFiltrados) {
      const nome = getSalaNomeDoItem(item);
      if (!grupos[nome]) grupos[nome] = [];
      grupos[nome].push(item);
    }
    return Object.entries(grupos)
      .sort(([a], [b]) => a.localeCompare(b, 'pt-BR'))
      .map(([nome, itens]) => [nome, [...itens].sort(ordenarPorLamic)]);
  })();

  const graficoSrc = `${API_URL}/graficos/valor-por-sala?t=${graficoKey}`;

  const renderItem = (item, mostrarSala = true) => {
    const expandido = expandidos.has(item.id);
    const componentes = Array.isArray(item.componentes) ? item.componentes : [];
    return (
      <li key={item.id} className="list-item">
        <div className="item-row">
          <div className="item-info">
            <p className="item-name">
              <span style={{ color: 'var(--primary-color)', fontWeight: '700' }}>
                {item.numero_patrimonio_lamic ? `#${item.numero_patrimonio_lamic}` : 'Sem LAMIC'}
              </span>{' '}
              - {item.nome}
            </p>
            <div className="item-details">
              {mostrarSala && <span><strong>Sala:</strong> {getSalaNomeDoItem(item)}</span>}
              <span><strong>Quantidade:</strong> {item.quantidade}</span>
              <span><strong>UFSM:</strong> {item.numero_patrimonio_ufsm || '—'}</span>
              {componentes.length > 0 && (
                <span className="componentes-badge">{componentes.length} {componentes.length === 1 ? 'componente' : 'componentes'}</span>
              )}
            </div>
          </div>
          <div className="item-value">{formatCurrencyBR(item.valor_total)}</div>
          <div className="item-actions">
            <button onClick={() => toggleExpandido(item.id)} className={`btn btn-small btn-expand ${expandido ? 'expanded' : ''}`} title="Componentes">
              {expandido ? '▲' : '▼'}{componentes.length > 0 ? ` ${componentes.length}` : ''}
            </button>
            <button onClick={() => prepararEdicao(item)} className="btn btn-primary btn-small">✏️</button>
            <button onClick={() => deletarItem(item.id)} className="btn btn-danger btn-small">🗑️</button>
          </div>
        </div>

        {expandido && (
          <div className="item-componentes">
            <div className="componentes-header">
              <span>Componentes / Partes</span>
              <button onClick={() => abrirModalComponente(item.id)} className="btn btn-success btn-small">
                ➕ Adicionar
              </button>
            </div>
            {componentes.length === 0 ? (
              <p className="componentes-empty">Nenhum componente cadastrado.</p>
            ) : (
              <table className="componentes-table">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Nº de Série</th>
                    <th>Qtd</th>
                    <th>Valor</th>
                    <th>Observação</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {componentes.map((c) => (
                    <tr key={c.id}>
                      <td>{c.nome}</td>
                      <td>{c.numero_serie || '—'}</td>
                      <td>{c.quantidade}</td>
                      <td>{c.valor ? formatCurrencyBR(c.valor) : '—'}</td>
                      <td>{c.observacao || '—'}</td>
                      <td className="componente-actions">
                        <button onClick={() => abrirModalComponente(item.id, c)} className="btn btn-primary btn-small">✏️</button>
                        <button onClick={() => deletarComponente(c.id)} className="btn btn-danger btn-small">🗑️</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </li>
    );
  };

  return (
    <div className="app-container">
      <header className="hero-header">
        <div className="hero-content">
          <img src="/logo_lamic.png" alt="LAMIC" className="logo-img" />
          <div className="hero-title">
            <h1 className="header-title">Sistema de Patrimônio</h1>
            <p className="header-subtitle">LAMIC - Laboratório de Análises Micotoxicológicas - UFSM</p>
          </div>
          <img src="/ufsm_png.png" alt="UFSM" className="logo-img" />
        </div>
      </header>

      <div className="app-main">
        <div className="section-header">
          <div className="section-header-left">
            <h3>📋 Lista de Patrimônios ({patrimoniosFiltrados.length})</h3>
            <div className="aba-group">
              <button className={`btn ${abaAtual === 'ativos' ? 'btn-primary' : 'btn-secondary'} btn-small`} onClick={() => setAbaAtual('ativos')}>🟢 Ativos</button>
              <button className={`btn ${abaAtual === 'inativos' ? 'btn-primary' : 'btn-secondary'} btn-small`} onClick={() => setAbaAtual('inativos')}>🔴 Inativos</button>
            </div>
          </div>
          <div className="button-group">
            <button onClick={abrirModalCadastro} className="btn btn-success btn-small">➕ Novo</button>
            <button onClick={exportarPDF} className="btn btn-danger btn-small">📄 PDF</button>
            <button onClick={abrirEstatisticas} className="btn btn-primary btn-small">📊 Estatísticas</button>
            <button onClick={() => setMostrarFiltros((v) => !v)} className={`btn btn-small ${filtrosAtivos > 0 ? 'btn-warning' : 'btn-secondary'}`}>
              🔍 Filtros{filtrosAtivos > 0 ? ` (${filtrosAtivos})` : ''}
            </button>
          </div>
        </div>

        {mostrarFiltros && (
          <div className="filter-panel">
            <div className="filter-grid">
              <div className="filter-field">
                <label className="filter-label">Nome</label>
                <input className="input" placeholder="Buscar por nome..." value={filtros.nome} onChange={(e) => setFiltro('nome', e.target.value)} />
              </div>
              <div className="filter-field">
                <label className="filter-label">Nº LAMIC</label>
                <input className="input" placeholder="Nº Patrimônio LAMIC" value={filtros.numero_patrimonio_lamic} onChange={(e) => setFiltro('numero_patrimonio_lamic', e.target.value)} />
              </div>
              <div className="filter-field">
                <label className="filter-label">Nº UFSM</label>
                <input className="input" placeholder="Nº Patrimônio UFSM" value={filtros.numero_patrimonio_ufsm} onChange={(e) => setFiltro('numero_patrimonio_ufsm', e.target.value)} />
              </div>
              <div className="filter-field">
                <label className="filter-label">Sala</label>
                <select className="input" value={filtros.sala_id} onChange={(e) => setFiltro('sala_id', e.target.value)}>
                  <option value="">Todas as salas</option>
                  {listaSalasParaSelect.map((sala, index) => {
                    const nome = getSalaNome(sala);
                    const id = getSalaId(sala);
                    if (!nome) return null;
                    return <option key={getSalaKey(sala, index)} value={String(id ?? '')}>{nome}</option>;
                  })}
                </select>
              </div>
              <div className="filter-field">
                <label className="filter-label">Qtd mínima</label>
                <input type="number" className="input" placeholder="0" min="0" value={filtros.quantidade_min} onChange={(e) => setFiltro('quantidade_min', e.target.value)} />
              </div>
              <div className="filter-field">
                <label className="filter-label">Qtd máxima</label>
                <input type="number" className="input" placeholder="∞" min="0" value={filtros.quantidade_max} onChange={(e) => setFiltro('quantidade_max', e.target.value)} />
              </div>
              <div className="filter-field">
                <label className="filter-label">Valor mín (R$)</label>
                <input type="number" className="input" placeholder="0,00" min="0" step="0.01" value={filtros.valor_min} onChange={(e) => setFiltro('valor_min', e.target.value)} />
              </div>
              <div className="filter-field">
                <label className="filter-label">Valor máx (R$)</label>
                <input type="number" className="input" placeholder="∞" min="0" step="0.01" value={filtros.valor_max} onChange={(e) => setFiltro('valor_max', e.target.value)} />
              </div>
            </div>
            {filtrosAtivos > 0 && (
              <div className="filter-footer">
                <button onClick={limparFiltros} className="btn btn-secondary btn-small">✖ Limpar filtros</button>
              </div>
            )}
          </div>
        )}

        {patrimoniosFiltrados.length === 0 ? (
          <div className="list-empty">
            <p style={{ fontSize: '1.1em' }}>📭 Nenhum item encontrado</p>
            <p style={{ fontSize: '0.9em' }}>
              {filtrosAtivos > 0 ? 'Tente ajustar os filtros aplicados' : 'Clique em "➕ Novo" para cadastrar o primeiro patrimônio'}
            </p>
          </div>
        ) : filtrosAtivos > 0 ? (
          <ul className="list">
            {patrimoniosFiltrados.map((item) => renderItem(item, true))}
          </ul>
        ) : (
          <div className="list">
            {itensAgrupados.map(([salaNome, itens]) => {
              const totalSala = itens.reduce((s, i) => s + Number(i.valor_total || 0), 0);
              return (
                <div key={salaNome} className="sala-group">
                  <div className="sala-group-header">
                    <span className="sala-group-nome">{salaNome}</span>
                    <span className="sala-group-meta">{itens.length} {itens.length === 1 ? 'item' : 'itens'} · {formatCurrencyBR(totalSala)}</span>
                  </div>
                  <ul className="list sala-group-list">
                    {itens.map((item) => renderItem(item, false))}
                  </ul>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal patrimônio */}
      {mostrarModal && (
        <div className="modal-overlay" onClick={fecharModal}>
          <div className="modal modal-wide" role="dialog" aria-modal="true" aria-labelledby="modal-title" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 id="modal-title">{idEdicao ? '✏️ Editar Patrimônio' : '➕ Novo Patrimônio'}</h3>
              <button type="button" onClick={fecharModal} className="modal-close" aria-label="Fechar">✕</button>
            </div>
            <form onSubmit={handleSubmit} className="form">
              <div className="modal-form-grid">
                <div className="form-field">
                  <label className="form-label">Nº Patrimônio LAMIC</label>
                  <input name="numero_patrimonio_lamic" placeholder="Opcional" value={form.numero_patrimonio_lamic} onChange={handleChange} className="input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Nº Patrimônio UFSM</label>
                  <input name="numero_patrimonio_ufsm" placeholder="Opcional" value={form.numero_patrimonio_ufsm} onChange={handleChange} className="input" />
                </div>
                <div className="form-field form-field-wide">
                  <label className="form-label">Nome do Ativo *</label>
                  <input name="nome" placeholder="Ex: Computador Dell OptiPlex" value={form.nome} onChange={handleChange} required className="input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Sala *</label>
                  <select name="sala_id" value={form.sala_id} onChange={handleChange} required className="input">
                    <option value="">Selecione uma sala</option>
                    {listaSalasParaSelect.map((sala, index) => {
                      const salaNome = getSalaNome(sala);
                      const salaId = getSalaId(sala);
                      if (!salaNome) return null;
                      return <option key={getSalaKey(sala, index)} value={String(salaId ?? '')}>{salaNome}</option>;
                    })}
                  </select>
                </div>
                <div className="form-field">
                  <label className="form-label">Quantidade</label>
                  <input type="number" name="quantidade" placeholder="1" value={form.quantidade} onChange={handleChange} className="input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Valor Total</label>
                  <input name="valor_total" placeholder="R$ 0,00" value={formatCurrencyBR(form.valor_total)} onChange={handleValorChange} inputMode="numeric" className="input" />
                </div>
                <div className="form-field">
                  <label className="form-label">&nbsp;</label>
                  <label className="checkbox-label">
                    <input type="checkbox" name="ativo" checked={form.ativo} onChange={(e) => setForm({ ...form, ativo: e.target.checked })} />
                    Item Ativo
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={fecharModal} className="btn btn-secondary">Cancelar</button>
                <button type="submit" className={`btn ${idEdicao ? 'btn-warning' : 'btn-success'}`}>
                  {idEdicao ? '💾 Salvar Alterações' : '✔ Cadastrar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal componente */}
      {modalComponente && (
        <div className="modal-overlay" onClick={fecharModalComponente}>
          <div className="modal modal-wide" role="dialog" aria-modal="true" aria-labelledby="modal-comp-title" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 id="modal-comp-title">{modalComponente.componente ? '✏️ Editar Componente' : '➕ Novo Componente'}</h3>
              <button type="button" onClick={fecharModalComponente} className="modal-close" aria-label="Fechar">✕</button>
            </div>
            <form onSubmit={handleSubmitComponente} className="form">
              <div className="modal-form-grid">
                <div className="form-field form-field-wide">
                  <label className="form-label">Nome *</label>
                  <input placeholder="Ex: Monitor, Bomba HPLC, CPU..." value={componenteForm.nome} onChange={(e) => setComponenteForm((p) => ({ ...p, nome: e.target.value }))} required className="input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Nº de Série</label>
                  <input placeholder="Opcional" value={componenteForm.numero_serie} onChange={(e) => setComponenteForm((p) => ({ ...p, numero_serie: e.target.value }))} className="input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Quantidade</label>
                  <input type="number" min="1" value={componenteForm.quantidade} onChange={(e) => setComponenteForm((p) => ({ ...p, quantidade: e.target.value }))} className="input" />
                </div>
                <div className="form-field">
                  <label className="form-label">Valor (R$)</label>
                  <input placeholder="R$ 0,00" value={formatCurrencyBR(componenteForm.valor)} onChange={handleValorComponenteChange} inputMode="numeric" className="input" />
                </div>
                <div className="form-field form-field-wide">
                  <label className="form-label">Observação</label>
                  <input placeholder="Opcional — modelo, condição, etc." value={componenteForm.observacao} onChange={(e) => setComponenteForm((p) => ({ ...p, observacao: e.target.value }))} className="input" />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={fecharModalComponente} className="btn btn-secondary">Cancelar</button>
                <button type="submit" className={`btn ${modalComponente.componente ? 'btn-warning' : 'btn-success'}`}>
                  {modalComponente.componente ? '💾 Salvar' : '✔ Adicionar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal estatísticas */}
      {mostrarEstatisticas && (
        <div className="modal-overlay" onClick={fecharEstatisticas}>
          <section className="stats-modal" role="dialog" aria-modal="true" aria-labelledby="stats-modal-title" onClick={(e) => e.stopPropagation()}>
            <div className="stats-modal-header">
              <h4 id="stats-modal-title">📈 Valor Total de Patrimônio por Sala</h4>
              <div className="stats-modal-actions">
                <button onClick={atualizarGrafico} className="btn btn-secondary btn-small" type="button">🔄 Atualizar</button>
                <button onClick={diminuirZoom} className="btn btn-secondary btn-small" type="button" aria-label="Diminuir zoom">➖</button>
                <button onClick={resetarZoom} className="btn btn-secondary btn-small" type="button" aria-label="Resetar zoom">100%</button>
                <button onClick={aumentarZoom} className="btn btn-secondary btn-small" type="button" aria-label="Aumentar zoom">➕</button>
                <span className="zoom-label">Zoom: {Math.round(zoomGrafico * 100)}%</span>
                <button onClick={fecharEstatisticas} className="btn btn-primary btn-small" type="button">✖ Fechar</button>
              </div>
            </div>
            {erroGrafico ? (
              <p className="stats-error">Não foi possível carregar o gráfico agora.</p>
            ) : (
              <div className="stats-image-viewport">
                <img src={graficoSrc} alt="Gráfico de valor total por sala" className="stats-image" style={{ width: `${zoomGrafico * 100}%`, maxWidth: 'none' }} onError={() => setErroGrafico(true)} />
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
