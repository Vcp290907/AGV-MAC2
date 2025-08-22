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

  const adicionarNovoItem = async (subCorredorId, posicao) => {
    const proximaTag = await gerarProximaTag();
    
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
    setImagemSelecionada(null);
    setPreviewImagem(null);
    setModoEdicao(true);
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

      if (imagemSelecionada) {
        nomeImagem = await uploadImagem(imagemSelecionada);
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
        alert(itemEditando.id ? 'Item atualizado com sucesso!' : 'Item criado com sucesso!');
        setModoEdicao(false);
        setItemEditando(null);
        setImagemSelecionada(null);
        setPreviewImagem(null);
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
  };

  const getSubCorredorSelecionadoInfo = () => {
    if (!subCorredorSelecionado) return null;
    
    const corredor = corredores.find(c => c.id === corredorSelecionado);
    const subCorredor = corredor?.subCorredores.find(s => s.id === subCorredorSelecionado);
    return subCorredor;
  };

  const renderizarConteudo = () => {
    if (!subCorredorSelecionado) {
      const corredor = corredores.find(c => c.id === corredorSelecionado);
      return (
        <div className="space-y-8">
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
                            <button
                              onClick={() => adicionarNovoItem(subCorredor.id, posicao)}
                              className="mt-2 px-2 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors"
                            >
                              Adicionar
                            </button>
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
                      <button
                        onClick={() => adicionarNovoItem(subCorredorSelecionado, posicao)}
                        className="px-3 py-2 bg-green-500 text-white text-sm rounded hover:bg-green-600 transition-colors"
                      >
                        Adicionar Item
                      </button>
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
          Disposição dos itens
        </h2>
      </div>

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

      {/* Conteúdo Principal */}
      <div className="min-h-96">
        {renderizarConteudo()}
      </div>

      {/* Modal de Edição Atualizado */}
      {modoEdicao && itemEditando && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
              {itemEditando.id ? `Editar: ${itemEditando.nome}` : 'Adicionar Novo Item'}
            </h3>
            
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

            {/* Botões do Modal */}
            <div className="flex gap-4 mt-6">
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
      )}
    </div>
  );
}