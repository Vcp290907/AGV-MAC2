import React, { useState, useEffect } from 'react';

export default function AdminUsuarios({ usuario }) {
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalAberto, setModalAberto] = useState(false);
  const [usuarioEditando, setUsuarioEditando] = useState(null);
  const [formData, setFormData] = useState({
    nome: '',
    username: '',
    password: '',
    perfil: 'funcionario',
    ativo: true
  });

  useEffect(() => {
    carregarUsuarios();
  }, []);

  const carregarUsuarios = async () => {
    try {
      const response = await fetch('http://10.56.218.93:5000/usuarios');
      const data = await response.json();
      setUsuarios(data);
    } catch (error) {
      setError('Erro ao carregar usuários');
    } finally {
      setLoading(false);
    }
  };

  const abrirModal = (usuarioParaEditar = null) => {
    if (usuarioParaEditar) {
      setUsuarioEditando(usuarioParaEditar);
      setFormData({
        nome: usuarioParaEditar.nome,
        username: usuarioParaEditar.username,
        password: '',
        perfil: usuarioParaEditar.perfil,
        ativo: usuarioParaEditar.ativo
      });
    } else {
      setUsuarioEditando(null);
      setFormData({
        nome: '',
        username: '',
        password: '',
        perfil: 'funcionario',
        ativo: true
      });
    }
    setModalAberto(true);
    setError('');
  };

  const fecharModal = () => {
    setModalAberto(false);
    setUsuarioEditando(null);
    setFormData({
      nome: '',
      username: '',
      password: '',
      perfil: 'funcionario',
      ativo: true
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const url = usuarioEditando
        ? `http://10.56.218.93:5000/usuarios/${usuarioEditando.id}`
        : 'http://10.56.218.93:5000/usuarios';

      const method = usuarioEditando ? 'PUT' : 'POST';

      const dadosEnvio = { ...formData };

      // Se estiver editando e a senha estiver vazia, remover do payload
      if (usuarioEditando && !dadosEnvio.password) {
        delete dadosEnvio.password;
      }

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dadosEnvio)
      });

      const data = await response.json();

      if (data.success) {
        await carregarUsuarios();
        fecharModal();
      } else {
        setError(data.message);
      }
    } catch (error) {
      setError('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  const excluirUsuario = async (usuarioId, nomeUsuario) => {
    if (!window.confirm(`Tem certeza que deseja excluir o usuário "${nomeUsuario}"?`)) {
      return;
    }

    try {
      const response = await fetch(`http://10.56.218.93:5000/usuarios/${usuarioId}`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (data.success) {
        await carregarUsuarios();
      } else {
        setError(data.message);
      }
    } catch (error) {
      setError('Erro ao excluir usuário');
    }
  };

  const alternarStatus = async (usuarioId, statusAtual) => {
    try {
      const response = await fetch(`http://10.56.218.93:5000/usuarios/${usuarioId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ativo: !statusAtual
        })
      });

      const data = await response.json();

      if (data.success) {
        await carregarUsuarios();
      } else {
        setError(data.message);
      }
    } catch (error) {
      setError('Erro ao alterar status do usuário');
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Carregando usuários...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800 dark:text-white">
            Administração de Usuários
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Gerencie usuários do sistema
          </p>
        </div>
        <button
          onClick={() => abrirModal()}
          className="bg-teal-500 hover:bg-teal-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          + Novo Usuário
        </button>
      </div>

      {/* Mensagem de erro */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Tabela de usuários */}
      <div className="bg-white dark:bg-gray-700 rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-600">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Nome
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Username
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Perfil
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Criado em
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
            {usuarios.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-600">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {user.nome}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900 dark:text-white">
                    {user.username}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.perfil === 'gerente'
                      ? 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-100'
                      : 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100'
                    }`}>
                    {user.perfil}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.ativo
                      ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                      : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                    }`}>
                    {user.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {new Date(user.created_at).toLocaleDateString('pt-BR')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                  <button
                    onClick={() => abrirModal(user)}
                    className="text-teal-600 hover:text-teal-900 dark:text-teal-400 dark:hover:text-teal-300"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => alternarStatus(user.id, user.ativo)}
                    className={`${user.ativo
                        ? 'text-yellow-600 hover:text-yellow-900 dark:text-yellow-400'
                        : 'text-green-600 hover:text-green-900 dark:text-green-400'
                      }`}
                  >
                    {user.ativo ? 'Desativar' : 'Ativar'}
                  </button>
                  <button
                    onClick={() => excluirUsuario(user.id, user.nome)}
                    className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                  >
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal para criar/editar usuário */}
      {modalAberto && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
              {usuarioEditando ? 'Editar Usuário' : 'Novo Usuário'}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Nome */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome Completo
                </label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white"
                  required
                />
              </div>

              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white"
                  required
                />
              </div>

              {/* Senha */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Senha {usuarioEditando && '(deixe em branco para manter a atual)'}
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white"
                  required={!usuarioEditando}
                />
              </div>

              {/* Perfil */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Perfil
                </label>
                <select
                  value={formData.perfil}
                  onChange={(e) => setFormData({ ...formData, perfil: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="funcionario">Funcionário</option>
                  <option value="gerente">Gerente</option>
                </select>
              </div>

              {/* Status (apenas ao editar) */}
              {usuarioEditando && (
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.ativo}
                      onChange={(e) => setFormData({ ...formData, ativo: e.target.checked })}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Usuário ativo
                    </span>
                  </label>
                </div>
              )}

              {/* Mensagem de erro */}
              {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-sm">
                  {error}
                </div>
              )}

              {/* Botões */}
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={fecharModal}
                  className="flex-1 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 py-2 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-teal-500 hover:bg-teal-600 text-white py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Salvando...' : usuarioEditando ? 'Atualizar' : 'Criar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
