import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../services/config';

export default function Pedidos() {
  const [pedidos, setPedidos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const carregarPedidos = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/pedidos`);
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const data = await res.json();
      setPedidos(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Não foi possível carregar os pedidos.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarPedidos();
  }, []);

  const statusBadge = (status) => {
    const map = {
      pendente: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      em_andamento: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      coletando: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300',
      concluido: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      cancelado: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    };
    const cls = map[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    return <span className={`px-2 py-1 rounded text-xs font-medium ${cls}`}>{tituloStatus(status)}</span>;
  };

  const tituloStatus = (s) => {
    switch (s) {
      case 'pendente': return 'Pendente';
      case 'em_andamento': return 'Em andamento';
      case 'coletando': return 'Coletando';
      case 'concluido': return 'Concluído';
      case 'cancelado': return 'Cancelado';
      default: return s;
    }
  };

  const formatarData = (dt) => {
    if (!dt) return '-';
    try {
      // dt pode vir como string ISO ou formato SQLite; tentar parse genérico
      const d = new Date(dt);
      if (!isNaN(d)) return d.toLocaleString();
    } catch {}
    return dt;
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Pedidos</h2>
          <p className="text-gray-600 dark:text-gray-400">Lista de todos os pedidos registrados</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={carregarPedidos}
            className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white"
          >
            Atualizar
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 overflow-x-auto">
        <table className="min-w-full text-left">
          <thead className="bg-gray-50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300 text-sm">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Usuário</th>
              <th className="px-4 py-3">Dispositivo</th>
              <th className="px-4 py-3">Itens</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Criado em</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700 text-sm">
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-gray-600 dark:text-gray-300">Carregando...</td>
              </tr>
            )}
            {!loading && error && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-red-600">{error}</td>
              </tr>
            )}
            {!loading && !error && pedidos.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-gray-600 dark:text-gray-300">Nenhum pedido encontrado.</td>
              </tr>
            )}
            {!loading && !error && pedidos.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">#{p.id}</td>
                <td className="px-4 py-3">
                  <div className="text-gray-900 dark:text-gray-100">{p.usuario_nome || '-'}</div>
                  {p.username && (
                    <div className="text-xs text-gray-500">@{p.username}</div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="text-gray-900 dark:text-gray-100">{p.dispositivo_nome || '-'}</div>
                  {p.dispositivo_codigo && (
                    <div className="text-xs text-gray-500">{p.dispositivo_codigo}</div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {(p.itens ? p.itens.split(',') : []).map((nome, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs">
                        {nome.trim()}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">{statusBadge(p.status)}</td>
                <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{formatarData(p.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
