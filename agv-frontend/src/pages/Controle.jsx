import React, { useState, useEffect } from 'react';

export default function Controle({ usuario }) {
  const [itens, setItens] = useState([]);
  const [itensSelecionados, setItensSelecionados] = useState([]);
  const [dispositivos, setDispositivos] = useState([]);
  const [dispositivoSelecionado, setDispositivoSelecionado] = useState('');
  const [pesquisa, setPesquisa] = useState('');
  const [loading, setLoading] = useState(false);

  // Carregar dados iniciais
  useEffect(() => {
    carregarItens();
    carregarDispositivos();
  }, []);

  const carregarItens = async () => {
    try {
      const response = await fetch('http://localhost:5000/itens');
      const data = await response.json();
      setItens(data);
    } catch (error) {
      console.error('Erro ao carregar itens:', error);
    }
  };

  const carregarDispositivos = async () => {
    try {
      const response = await fetch('http://localhost:5000/dispositivos/disponiveis');
      const data = await response.json();
      setDispositivos(data);
    } catch (error) {
      console.error('Erro ao carregar dispositivos:', error);
    }
  };

  const pesquisarItens = async () => {
    if (!pesquisa.trim()) {
      carregarItens();
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/itens/pesquisar?q=${pesquisa}`);
      const data = await response.json();
      setItens(data);
    } catch (error) {
      console.error('Erro ao pesquisar:', error);
    }
  };

  const adicionarItem = (item) => {
    if (itensSelecionados.length >= 4) {
      alert('Máximo 4 itens por viagem!');
      return;
    }

    if (itensSelecionados.find(i => i.id === item.id)) {
      alert('Item já selecionado!');
      return;
    }

    setItensSelecionados([...itensSelecionados, item]);
  };

  const removerItem = (itemId) => {
    setItensSelecionados(itensSelecionados.filter(item => item.id !== itemId));
  };

  const enviarPedido = async () => {
    if (itensSelecionados.length === 0) {
      alert('Selecione pelo menos um item!');
      return;
    }

    if (!dispositivoSelecionado) {
      alert('Selecione um dispositivo!');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/pedidos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          usuario_id: usuario.id,  // ← Usar ID do usuário logado
          itens: itensSelecionados.map(item => item.id),
          dispositivo_id: dispositivoSelecionado
        })
      });

      const data = await response.json();
      if (data.success) {
        alert('Pedido enviado com sucesso!');
        setItensSelecionados([]);
        setDispositivoSelecionado('');
        carregarDispositivos();
      } else {
        alert('Erro ao enviar pedido: ' + data.error);
      }
    } catch (error) {
      alert('Erro ao enviar pedido');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      disponivel: 'text-green-600',
      ocupado: 'text-yellow-600',
      manutencao: 'text-red-600'
    };
    return colors[status] || 'text-gray-600';
  };

  const getStatusText = (status) => {
    const texts = {
      disponivel: 'Disponível',
      ocupado: 'Ocupado',
      manutencao: 'Manutenção'
    };
    return texts[status] || status;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Controles superiores */}
      <div className="flex gap-4">
        <div className="min-w-0 flex-shrink-0">
          <select 
            value={dispositivoSelecionado}
            onChange={(e) => setDispositivoSelecionado(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="">Selecione o Dispositivo</option>
            {dispositivos.map(dispositivo => (
              <option key={dispositivo.id} value={dispositivo.id}>
                {dispositivo.nome} - {dispositivo.codigo} (🔋{dispositivo.bateria}%)
              </option>
            ))}
          </select>
        </div>
        
        <div className="flex gap-2 flex-1">
          <input
            type="text"
            placeholder="Pesquise o item que deseja"
            value={pesquisa}
            onChange={(e) => setPesquisa(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && pesquisarItens()}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg flex-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
          <button
            onClick={pesquisarItens}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Pesquisar
          </button>
        </div>
      </div>

      {/* Dispositivo selecionado */}
      {dispositivoSelecionado && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">Dispositivo Selecionado:</h3>
          {dispositivos.find(d => d.id == dispositivoSelecionado) && (
            <div className="text-blue-800 dark:text-blue-200">
              <p><strong>{dispositivos.find(d => d.id == dispositivoSelecionado).nome}</strong></p>
              <p>Código: {dispositivos.find(d => d.id == dispositivoSelecionado).codigo}</p>
              <p>Bateria: {dispositivos.find(d => d.id == dispositivoSelecionado).bateria}%</p>
              <p>Localização: {dispositivos.find(d => d.id == dispositivoSelecionado).localizacao}</p>
            </div>
          )}
        </div>
      )}

      {/* Lista de itens disponíveis */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {itens.map(item => (
          <div
            key={item.id}
            onClick={() => adicionarItem(item)}
            className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 text-center bg-white dark:bg-gray-800 transition-colors"
          >
            <div className="w-16 h-16 bg-gray-200 dark:bg-gray-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
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
            <h3 className="font-medium text-gray-900 dark:text-white">{item.nome}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">Tag: {item.tag}</p>
          </div>
        ))}
      </div>

      {/* Itens selecionados */}
      <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-6 bg-white dark:bg-gray-800">
        <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Itens selecionados</h3>
        
        {itensSelecionados.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">Nenhum item selecionado</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {itensSelecionados.map(item => (
              <div key={item.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 text-center relative bg-gray-50 dark:bg-gray-700">
                <button
                  onClick={() => removerItem(item.id)}
                  className="absolute top-2 right-2 text-red-500 hover:text-red-700 font-bold"
                >
                  ✕
                </button>
                <div className="w-16 h-16 bg-teal-500 rounded-lg mx-auto mb-2 flex items-center justify-center text-white">
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
                <h4 className="font-medium text-gray-900 dark:text-white">{item.nome}</h4>
                <p className="text-sm text-gray-500 dark:text-gray-400">Tag: {item.tag}</p>
              </div>
            ))}
          </div>
        )}
        
        <p className="text-red-500 text-center mb-4">
          Clique para retirar | Max 4 itens ({itensSelecionados.length}/4)
        </p>
      </div>

      {/* Botões de ação */}
      <div className="flex justify-center gap-4">
        <button
          onClick={() => {
            setItensSelecionados([]);
            setDispositivoSelecionado('');
          }}
          className="px-8 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          Cancelar
        </button>
        
        <button className="px-8 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors">
          Criar rotina
        </button>
        
        <button
          onClick={enviarPedido}
          disabled={loading || itensSelecionados.length === 0 || !dispositivoSelecionado}
          className="px-8 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Enviando...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
}