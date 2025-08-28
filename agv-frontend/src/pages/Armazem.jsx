import React, { useState, useEffect } from 'react';

export default function Armazem({ usuario }) {
  const [itens, setItens] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [corredorSelecionado, setCorredorSelecionado] = useState('1');
  const [subCorredorSelecionado, setSubCorredorSelecionado] = useState('');
  const [modoEdicao, setModoEdicao] = useState(false);
  const [itemEditando, setItemEditando] = useState(null);
  const [loading, setLoading] = useState(false);
  const [imagemSelecionada, setImagemSelecionada] = useState(null);
  const [previewImagem, setPreviewImagem] = useState(null);
  const [abaAtiva, setAbaAtiva] = useState('disposicao'); // 'disposicao' ou 'lista'
  const [termoPesquisa, setTermoPesquisa] = useState('');
  const [itensFiltrados, setItensFiltrados] = useState([]);
  const [tipoAdicao, setTipoAdicao] = useState('novo'); // 'novo' ou 'baseado'
  const [itemModelo, setItemModelo] = useState(null);
  const [mostrarModalSeletor, setMostrarModalSeletor] = useState(false);
  const [posicaoDestino, setPosicaoDestino] = useState({ subCorredor: '', posicao: 1 });

  // Estrutura do armazém
  const corredores = [
    {
      id: '1',
      nome: 'Corredor A',
      subCorredores: [
        { id: '1', nome: 'Sub-corredor A1' },
        { id: '2', nome: 'Sub-corredor A2' },
        { id: '3', nome: 'Sub-corredor A3' }
      ]
    }
  ];

  const POSICOES_POR_SUBCORREDOR = 4;

  useEffect(() => {
    carregarItens();
    carregarCategorias();
  }, []);

  useEffect(() => {
    if (termoPesquisa.trim() === '') {
      setItensFiltrados(itens);
    } else {
      const filtrados = itens.filter(item => 
        item.nome.toLowerCase().includes(termoPesquisa.toLowerCase()) ||
        item.tag.toLowerCase().includes(termoPesquisa.toLowerCase()) ||
        item.categoria.toLowerCase().includes(termoPesquisa.toLowerCase())
      );
      setItensFiltrados(filtrados);
    }
  }, [itens, termoPesquisa]);

  const carregarItens = async () => {
    try {
      const response = await fetch('http://localhost:5000/armazem/itens');
      const data = await response.json();
      setItens(data);
    } catch (error) {
      console.error('Erro ao carregar itens:', error);
    }
  };

  const carregarCategorias = async () => {
    try {
      const response = await fetch('http://localhost:5000/armazem/categorias');
      const data = await response.json();
      setCategorias(data);
    } catch (error) {
      console.error('Erro ao carregar categorias:', error);
      // Categorias padrão se API falhar
      setCategorias([
        { id: 1, nome: 'Fixação' },
        { id: 2, nome: 'Eletrônicos' },
        { id: 3, nome: 'Ferramentas' },
        { id: 4, nome: 'Diversos' }
      ]);
    }
  };

  const gerarProximaTag = async () => {
    try {
      const response = await fetch('http://localhost:5000/armazem/proxima-tag');
      const data = await response.json();
      return data.tag;
    } catch (error) {
      console.error('Erro ao gerar próxima tag:', error);
      return `TAG${Date.now()}`;
    }
  };

  const gerarPosicoesSubCorredor = (subCorredorId) => {
    const itensDoSubCorredor = itens.filter(item => 
      item.corredor === corredorSelecionado && 
      item.sub_corredor === subCorredorId
    );

    const posicoes = [];
    for (let i = 1; i <= POSICOES_POR_SUBCORREDOR; i++) {
      const itemNaPosicao = itensDoSubCorredor.find(item => item.posicao_x === i);
      posicoes.push({
        posicao: i,
        item: itemNaPosicao || null,
        vazia: !itemNaPosicao
      });
    }

    return posicoes;
  };

  const handleEditarItem = (item) => {
    setItemEditando({
      ...item,
      novo_corredor: item.corredor || '1',
      novo_sub_corredor: item.sub_corredor || '1',
      nova_posicao_x: item.posicao_x || 1,
      nova_posicao_y: item.posicao_y || 1
    });
    setImagemSelecionada(null);
    setPreviewImagem(null);
    setModoEdicao(true);
  };

  const adicionarNovoItem = async (subCorredorId, posicao, itemBaseado = null) => {
    const proximaTag = await gerarProximaTag();
    
    if (itemBaseado) {
      // Criar item baseado em um existente
      setItemEditando({
        id: null,
        nome: itemBaseado.nome,
        tag: proximaTag,
        categoria: itemBaseado.categoria,
        imagem: itemBaseado.imagem,
        novo_corredor: corredorSelecionado,
        novo_sub_corredor: subCorredorId,
        nova_posicao_x: posicao,
        nova_posicao_y: 1
      });
      setTipoAdicao('baseado');
      setItemModelo(itemBaseado);
    } else {
      // Criar item completamente novo
      setItemEditando({
        id: null,
        nome: '',
        tag: proximaTag,
        categoria: categorias[0]?.nome || 'Diversos',
        imagem: null,
        novo_corredor: corredorSelecionado,
        novo_sub_corredor: subCorredorId,
        nova_posicao_x: posicao,
        nova_posicao_y: 1
      });
      setTipoAdicao('novo');
      setItemModelo(null);
    }
    
    setImagemSelecionada(null);
    setPreviewImagem(null);
    setModoEdicao(true);
  };

  const mostrarSeletorItemModelo = (subCorredorId, posicao) => {
    setPosicaoDestino({ subCorredor: subCorredorId, posicao: posicao });
    setMostrarModalSeletor(true);
  };

  const selecionarItemModelo = async (itemSelecionado) => {
    setMostrarModalSeletor(false);
    await adicionarNovoItem(posicaoDestino.subCorredor, posicaoDestino.posicao, itemSelecionado);
  };

  const handleImagemChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('Por favor, selecione um arquivo de imagem válido');
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        alert('A imagem deve ter no máximo 5MB');
        return;
      }

      setImagemSelecionada(file);
      
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewImagem(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadImagem = async (file) => {
    const formData = new FormData();
    formData.append('imagem', file);

    const response = await fetch('http://localhost:5000/armazem/upload-imagem', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    if (data.success) {
      return data.filename;
    } else {
      throw new Error(data.error || 'Erro ao fazer upload da imagem');
    }
  };

  const salvarEdicao = async () => {
    if (!itemEditando) return;

    if (!itemEditando.nome.trim()) {
      alert('Nome é obrigatório');
      return;
    }

    setLoading(true);
    try {
      let nomeImagem = itemEditando.imagem;

      // Se uma nova imagem foi selecionada, fazer upload
      if (imagemSelecionada) {
        nomeImagem = await uploadImagem(imagemSelecionada);
      }
      // Se é baseado em item e não selecionou nova imagem, manter a imagem do modelo
      else if (tipoAdicao === 'baseado' && itemModelo && !itemEditando.id) {
        nomeImagem = itemModelo.imagem;
      }

      const url = itemEditando.id 
        ? `http://localhost:5000/armazem/itens/${itemEditando.id}`
        : 'http://localhost:5000/armazem/itens';
      
      const method = itemEditando.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: itemEditando.nome,
          tag: itemEditando.tag,
          categoria: itemEditando.categoria,
          imagem: nomeImagem,
          corredor: itemEditando.novo_corredor,
          sub_corredor: itemEditando.novo_sub_corredor,
          posicao_x: itemEditando.nova_posicao_x,
          posicao_y: itemEditando.nova_posicao_y,
          disponivel: 1
        })
      });

      const data = await response.json();
      if (data.success) {
        alert(itemEditando.id ? 'Item atualizado com sucesso!' : 
              tipoAdicao === 'baseado' ? 'Nova instância criada com sucesso!' : 
              'Item criado com sucesso!');
        setModoEdicao(false);
        setItemEditando(null);
        setImagemSelecionada(null);
        setPreviewImagem(null);
        setTipoAdicao('novo');
        setItemModelo(null);
        carregarItens();
      } else {
        alert('Erro ao salvar item: ' + data.error);
      }
    } catch (error) {
      alert('Erro ao salvar alterações: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const excluirItem = async (itemId) => {
    if (!window.confirm('Tem certeza que deseja excluir este item?')) return;

    try {
      const response = await fetch(`http://localhost:5000/armazem/itens/${itemId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        alert('Item excluído com sucesso!');
        carregarItens();
      } else {
        alert('Erro ao excluir item: ' + data.error);
      }
    } catch (error) {
      alert('Erro ao excluir item');
    }
  };

  const cancelarEdicao = () => {
    setModoEdicao(false);
    setItemEditando(null);
    setImagemSelecionada(null);
    setPreviewImagem(null);
    setTipoAdicao('novo');
    setItemModelo(null);
  };

  const getSubCorredorSelecionadoInfo = () => {
    if (!subCorredorSelecionado) return null;
    
    const corredor = corredores.find(c => c.id === corredorSelecionado);
    const subCorredor = corredor?.subCorredores.find(s => s.id === subCorredorSelecionado);
    return subCorredor;
  };

  const renderizarListaItens = () => {
    return (
      <div className="space-y-6">
        {/* Barra de pesquisa */}
        <div className="max-w-md mx-auto">
          <div className="relative">
            <input
              type="text"
              placeholder="Pesquisar por nome, tag ou categoria..."
              value={termoPesquisa}
              onChange={(e) => setTermoPesquisa(e.target.value)}
              className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Estatísticas */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <div className="text-center">
            <p className="text-blue-700 dark:text-blue-300">
              <span className="font-semibold">{itensFiltrados.length}</span> 
              {termoPesquisa ? ' itens encontrados' : ' itens cadastrados no total'}
            </p>
          </div>
        </div>

        {/* Lista de itens */}
        {itensFiltrados.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📦</div>
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              {termoPesquisa ? 'Nenhum item encontrado para sua pesquisa' : 'Nenhum item cadastrado'}
            </p>
          </div>
        ) : (
          <div className="max-h-[60vh] overflow-y-auto pr-2">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {itensFiltrados.map(item => (
                <div
                  key={item.id}
                  className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6 hover:shadow-lg transition-shadow"
                >
                  {/* Imagem do item */}
                  <div className="w-24 h-24 bg-gray-200 dark:bg-gray-600 rounded-lg mx-auto mb-4 flex items-center justify-center overflow-hidden">
                    {item.imagem ? (
                      <img 
                        src={`http://localhost:5000/static/images/${item.imagem}`} 
                        alt={item.nome}
                        className="w-full h-full object-cover rounded-lg"
                      />
                    ) : (
                      <span className="text-3xl">📦</span>
                    )}
                  </div>

                  {/* Informações do item */}
                  <div className="text-center space-y-2">
                    <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
                      {item.nome}
                    </h3>
                    
                    <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                      <p><span className="font-medium">Tag:</span> {item.tag}</p>
                      <p><span className="font-medium">Categoria:</span> {item.categoria}</p>
                      <p>
                        <span className="font-medium">Localização:</span> 
                        {item.corredor ? ` Corredor ${item.corredor}, Sub ${item.sub_corredor}, Pos ${item.posicao_x}` : ' Não definida'}
                      </p>
                    </div>

                    {/* Status */}
                    <div className="flex justify-center mt-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        item.disponivel 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                      }`}>
                        {item.disponivel ? 'Disponível' : 'Indisponível'}
                      </span>
                    </div>

                    {/* Botões de ação (apenas para gerentes) */}
                    {usuario.perfil === 'gerente' && (
                      <div className="flex gap-2 mt-4 justify-center">
                        <button
                          onClick={() => handleEditarItem(item)}
                          className="px-4 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                          Editar
                        </button>
                        <button
                          onClick={() => excluirItem(item.id)}
                          className="px-4 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          Excluir
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderizarConteudo = () => {
    if (!subCorredorSelecionado) {
      const corredor = corredores.find(c => c.id === corredorSelecionado);
      return (
        <div className="max-h-[70vh] overflow-y-auto pr-2 space-y-8">
          {corredor?.subCorredores.map(subCorredor => {
            const posicoes = gerarPosicoesSubCorredor(subCorredor.id);
            const itensCount = posicoes.filter(p => !p.vazia).length;
            
            return (
              <div key={subCorredor.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  {subCorredor.nome} ({itensCount}/{POSICOES_POR_SUBCORREDOR} posições ocupadas)
                </h3>
                
                <div className="grid grid-cols-4 gap-4">
                  {posicoes.map(({ posicao, item, vazia }) => (
                    <div
                      key={posicao}
                      className={`border-2 border-dashed rounded-lg p-4 text-center min-h-32 flex flex-col justify-center ${
                        vazia 
                          ? 'border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800' 
                          : 'border-green-300 dark:border-green-600 bg-white dark:bg-gray-800'
                      }`}
                    >
                      {vazia ? (
                        <>
                          <div className="text-gray-400 text-3xl mb-2">➕</div>
                          <p className="text-gray-500 dark:text-gray-400 text-sm">
                            Posição {posicao}
                          </p>
                          <p className="text-gray-500 dark:text-gray-400 text-xs">
                            Vazia
                          </p>
                          {usuario.perfil === 'gerente' && (
                            <div className="space-y-1">
                              <button
                                onClick={() => adicionarNovoItem(subCorredor.id, posicao)}
                                className="w-full px-2 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors"
                              >
                                Novo Item
                              </button>
                              <button
                                onClick={() => mostrarSeletorItemModelo(subCorredor.id, posicao)}
                                className="w-full px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                              >
                                Baseado em Item
                              </button>
                            </div>
                          )}
                        </>
                      ) : (
                        <>
                          <div className="w-12 h-12 bg-gray-200 dark:bg-gray-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                            {item.imagem ? (
                              <img 
                                src={`http://localhost:5000/static/images/${item.imagem}`} 
                                alt={item.nome}
                                className="w-full h-full object-cover rounded-lg"
                              />
                            ) : (
                              <span className="text-xl">📦</span>
                            )}
                          </div>
                          <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                            {item.nome}
                          </h4>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Tag: {item.tag}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Pos: {posicao}
                          </p>
                          
                          {usuario.perfil === 'gerente' && (
                            <div className="flex gap-1 mt-2">
                              <button
                                onClick={() => handleEditarItem(item)}
                                className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                              >
                                Editar
                              </button>
                              <button
                                onClick={() => excluirItem(item.id)}
                                className="px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors"
                              >
                                Excluir
                              </button>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      );
    } else {
      const subCorredorInfo = getSubCorredorSelecionadoInfo();
      const posicoes = gerarPosicoesSubCorredor(subCorredorSelecionado);
      const itensCount = posicoes.filter(p => !p.vazia).length;

      return (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-6">
          <h3 className="text-xl font-medium text-gray-900 dark:text-white mb-6 text-center">
            {subCorredorInfo?.nome} ({itensCount}/{POSICOES_POR_SUBCORREDOR} posições ocupadas)
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            {posicoes.map(({ posicao, item, vazia }) => (
              <div
                key={posicao}
                className={`border-2 border-dashed rounded-lg p-6 text-center min-h-40 flex flex-col justify-center ${
                  vazia 
                    ? 'border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800' 
                    : 'border-green-300 dark:border-green-600 bg-white dark:bg-gray-700'
                }`}
              >
                {vazia ? (
                  <>
                    <div className="text-gray-400 text-4xl mb-3">➕</div>
                    <p className="text-gray-500 dark:text-gray-400 text-lg font-medium">
                      Posição {posicao}
                    </p>
                    <p className="text-gray-500 dark:text-gray-400 text-sm mb-3">
                      Vazia
                    </p>
                    {usuario.perfil === 'gerente' && (
                      <div className="space-y-2">
                        <button
                          onClick={() => adicionarNovoItem(subCorredorSelecionado, posicao)}
                          className="w-full px-3 py-2 bg-green-500 text-white text-sm rounded hover:bg-green-600 transition-colors"
                        >
                          Novo Item
                        </button>
                        <button
                          onClick={() => mostrarSeletorItemModelo(subCorredorSelecionado, posicao)}
                          className="w-full px-3 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                        >
                          Baseado em Item
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="w-16 h-16 bg-gray-200 dark:bg-gray-600 rounded-lg mx-auto mb-3 flex items-center justify-center">
                      {item.imagem ? (
                        <img 
                          src={`http://localhost:5000/static/images/${item.imagem}`} 
                          alt={item.nome}
                          className="w-full h-full object-cover rounded-lg"
                        />
                      ) : (
                        <span className="text-2xl">📦</span>
                      )}
                    </div>
                    <h4 className="font-medium text-gray-900 dark:text-white text-lg">
                      {item.nome}
                    </h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                      Tag: {item.tag}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                      Posição: {posicao}
                    </p>
                    
                    {usuario.perfil === 'gerente' && (
                      <div className="flex gap-2 justify-center">
                        <button
                          onClick={() => handleEditarItem(item)}
                          className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => excluirItem(item.id)}
                          className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
                        >
                          Excluir
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      );
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Cabeçalho */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Gerenciamento do Armazém
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Gerencie a disposição e listagem dos itens do armazém
        </p>
      </div>

      {/* Abas de Navegação */}
      <div className="flex justify-center">
        <div className="inline-flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setAbaAtiva('disposicao')}
            className={`px-6 py-2 rounded-md font-medium transition-colors ${
              abaAtiva === 'disposicao'
                ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Disposição dos Itens
          </button>
          <button
            onClick={() => setAbaAtiva('lista')}
            className={`px-6 py-2 rounded-md font-medium transition-colors ${
              abaAtiva === 'lista'
                ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            Lista de Itens
          </button>
        </div>
      </div>

      {/* Conteúdo das Abas */}
      {abaAtiva === 'disposicao' ? (
        <div className="space-y-6">
          {/* Seletores de Corredor */}
          <div className="flex gap-4 items-center">
            <div className="flex items-center gap-2">
              <label className="text-gray-700 dark:text-gray-300 font-medium">
                Corredor:
              </label>
              <select
                value={corredorSelecionado}
                onChange={(e) => {
                  setCorredorSelecionado(e.target.value);
                  setSubCorredorSelecionado('');
                }}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {corredores.map(corredor => (
                  <option key={corredor.id} value={corredor.id}>
                    {corredor.nome}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-gray-700 dark:text-gray-300 font-medium">
                Sub corredor:
              </label>
              <select
                value={subCorredorSelecionado}
                onChange={(e) => setSubCorredorSelecionado(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Selecione um sub-corredor</option>
                {corredores
                  .find(c => c.id === corredorSelecionado)
                  ?.subCorredores.map(sub => (
                    <option key={sub.id} value={sub.id}>
                      {sub.nome}
                    </option>
                  ))}
              </select>
            </div>
          </div>

          {/* Conteúdo Principal - Disposição */}
          <div className="min-h-96 max-h-[calc(100vh-300px)] overflow-y-auto">
            {renderizarConteudo()}
          </div>
        </div>
      ) : (
        /* Conteúdo Principal - Lista */
        <div className="min-h-96 max-h-[calc(100vh-300px)]">
          {renderizarListaItens()}
        </div>
      )}

      {/* Modal Seletor de Item Modelo */}
      {mostrarModalSeletor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
            {/* Cabeçalho fixo */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-600">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                Selecionar Item como Modelo
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Escolha um item existente para criar uma nova instância com TAG diferente
              </p>
            </div>
            
            {/* Conteúdo com scroll */}
            <div className="flex-1 overflow-y-auto p-6">
              {itens.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-gray-400 text-6xl mb-4">📦</div>
                  <p className="text-gray-500 dark:text-gray-400 text-lg">
                    Nenhum item cadastrado ainda
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {itens.map(item => (
                    <div
                      key={item.id}
                      className="bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => selecionarItemModelo(item)}
                    >
                      {/* Imagem do item */}
                      <div className="w-16 h-16 bg-gray-200 dark:bg-gray-600 rounded-lg mx-auto mb-3 flex items-center justify-center overflow-hidden">
                        {item.imagem ? (
                          <img 
                            src={`http://localhost:5000/static/images/${item.imagem}`} 
                            alt={item.nome}
                            className="w-full h-full object-cover rounded-lg"
                          />
                        ) : (
                          <span className="text-2xl">📦</span>
                        )}
                      </div>

                      {/* Informações do item */}
                      <div className="text-center space-y-1">
                        <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                          {item.nome}
                        </h4>
                        <div className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                          <p><span className="font-medium">Tag:</span> {item.tag}</p>
                          <p><span className="font-medium">Categoria:</span> {item.categoria}</p>
                        </div>
                        
                        <button className="w-full mt-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors">
                          Selecionar
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Botões fixos na parte inferior */}
            <div className="p-6 border-t border-gray-200 dark:border-gray-600">
              <button
                onClick={() => setMostrarModalSeletor(false)}
                className="w-full px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Edição Atualizado */}
      {modoEdicao && itemEditando && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-lg max-h-[90vh] flex flex-col">
            {/* Cabeçalho fixo */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-600">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                {itemEditando.id ? `Editar: ${itemEditando.nome}` : 
                 tipoAdicao === 'baseado' ? `Nova Instância de: ${itemEditando.nome}` : 
                 'Adicionar Novo Item'}
              </h3>
              {tipoAdicao === 'baseado' && itemModelo && (
                <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                  Baseado no item: {itemModelo.nome} (Tag original: {itemModelo.tag})
                </p>
              )}
            </div>
            
            {/* Conteúdo com scroll */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
              {/* Upload de Imagem */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Imagem do Item:
                </label>
                
                {/* Preview da imagem */}
                <div className="mb-3">
                  {previewImagem || itemEditando.imagem ? (
                    <div className="w-32 h-32 mx-auto bg-gray-200 dark:bg-gray-600 rounded-lg overflow-hidden">
                      <img 
                        src={previewImagem || `http://localhost:5000/static/images/${itemEditando.imagem}`}
                        alt="Preview"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="w-32 h-32 mx-auto bg-gray-200 dark:bg-gray-600 rounded-lg flex items-center justify-center">
                      <span className="text-4xl text-gray-400">📦</span>
                    </div>
                  )}
                </div>

                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImagemChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Aceita JPG, PNG, GIF (máximo 5MB)
                </p>
              </div>

              {/* Nome */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome: *
                </label>
                <input
                  type="text"
                  value={itemEditando.nome}
                  onChange={(e) => setItemEditando({...itemEditando, nome: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Nome do item"
                />
              </div>

              {/* Tag (somente leitura para novos itens) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tag:
                </label>
                <input
                  type="text"
                  value={itemEditando.tag}
                  onChange={(e) => setItemEditando({...itemEditando, tag: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Tag única do item"
                  readOnly={!itemEditando.id} // Somente leitura para novos itens
                />
                {!itemEditando.id && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Tag gerada automaticamente
                  </p>
                )}
              </div>

              {/* Categoria */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Categoria: *
                </label>
                <select
                  value={itemEditando.categoria}
                  onChange={(e) => setItemEditando({...itemEditando, categoria: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {categorias.map(categoria => (
                    <option key={categoria.id} value={categoria.nome}>
                      {categoria.nome}
                    </option>
                  ))}
                </select>
              </div>

              {/* Localização */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Corredor:
                  </label>
                  <select
                    value={itemEditando.novo_corredor}
                    onChange={(e) => setItemEditando({...itemEditando, novo_corredor: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    {corredores.map(corredor => (
                      <option key={corredor.id} value={corredor.id}>
                        {corredor.nome}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Sub-corredor:
                  </label>
                  <select
                    value={itemEditando.novo_sub_corredor}
                    onChange={(e) => setItemEditando({...itemEditando, novo_sub_corredor: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    {corredores
                      .find(c => c.id === itemEditando.novo_corredor)
                      ?.subCorredores.map(sub => (
                        <option key={sub.id} value={sub.id}>
                          {sub.nome}
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              {/* Posição */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Posição (1-4):
                </label>
                <select
                  value={itemEditando.nova_posicao_x}
                  onChange={(e) => setItemEditando({...itemEditando, nova_posicao_x: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {[1, 2, 3, 4].map(pos => (
                    <option key={pos} value={pos}>Posição {pos}</option>
                  ))}
                </select>
              </div>
              </div>
            </div>

            {/* Botões do Modal - Fixos na parte inferior */}
            <div className="p-6 border-t border-gray-200 dark:border-gray-600">
              <div className="flex gap-4">
                <button
                  onClick={cancelarEdicao}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={salvarEdicao}
                  disabled={loading || !itemEditando.nome.trim()}
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Salvando...' : 'Salvar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}