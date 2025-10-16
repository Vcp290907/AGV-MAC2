import React from 'react';

export default function Sidebar({ usuario, paginaAtiva, setPaginaAtiva, onLogout, darkMode, toggleDarkMode }) {
  const menusGerente = [
    { id: 'controle', nome: 'Controle', icone: '📱' },
    { id: 'analise', nome: 'Análise', icone: '📊' },
    { id: 'armazem', nome: 'Armazém', icone: '📦' },
    { id: 'pedidos', nome: 'Pedidos', icone: '🧾' },
    { id: 'admin-usuarios', nome: 'Usuários', icone: '👥' },
    { id: 'status', nome: 'Status', icone: 'ℹ️' }
  ];

  const menusFuncionario = [
    { id: 'controle', nome: 'Controle', icone: '📱' },
    { id: 'status', nome: 'Status', icone: 'ℹ️' }
  ];

  const menus = usuario.perfil === 'gerente' ? menusGerente : menusFuncionario;

  return (
    <div className="w-64 bg-white dark:bg-gray-800 shadow-lg transition-colors flex flex-col min-h-screen">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center">
          <span className="bg-teal-500 text-white px-3 py-1 rounded text-sm font-bold mr-2">
            MAC
          </span>
          <span className="text-xl font-bold text-gray-800 dark:text-white">
            DASHBOARD
          </span>
        </div>
      </div>

      {/* Páginas */}
      <div className="p-4 flex-1 overflow-auto">
        <h3 className="text-gray-400 dark:text-gray-500 text-sm font-medium mb-4 uppercase">
          Páginas
        </h3>
        
        <nav className="space-y-2">
          {menus.map((menu) => (
            <button
              key={menu.id}
              onClick={() => setPaginaAtiva(menu.id)}
              className={`w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors ${
                paginaAtiva === menu.id
                  ? 'bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300 border-l-4 border-teal-500'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <span className="mr-3 text-lg">{menu.icone}</span>
              <span className="font-medium">{menu.nome}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Botões no rodapé */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex space-x-2">
        {/* Botão Dark Mode */}
        <button
          onClick={toggleDarkMode}
          className="flex items-center justify-center w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          title={darkMode ? 'Modo Claro' : 'Modo Escuro'}
        >
          <span className="text-xl">
            {darkMode ? '☀️' : '🌛'}
          </span>
        </button>

        {/* Botão Logout */}
        <button
          onClick={onLogout}
          className="flex items-center justify-center w-12 h-12 bg-red-500 hover:bg-red-600 rounded-lg text-white transition-colors"
          title="Sair"
        >
          <span className="text-xl">SAIR</span>
        </button>
      </div>
    </div>
  );
}