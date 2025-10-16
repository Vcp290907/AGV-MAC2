import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import Controle from './Controle';
import Armazem from './Armazem';
import AdminUsuarios from './AdminUsuarios';
import Status from './Status';
import Analise from './Analise';
import Pedidos from './Pedidos';

export default function Dashboard({ usuario, onLogout, darkMode, toggleDarkMode }) {
  const [paginaAtiva, setPaginaAtiva] = useState('controle');

  return (
    <div className="flex min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors">
      <Sidebar 
        usuario={usuario} 
        paginaAtiva={paginaAtiva}
        setPaginaAtiva={setPaginaAtiva}
        onLogout={onLogout}
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
      />
      
      <div className="flex-1 flex flex-col min-h-0">
        <div className="bg-white dark:bg-gray-800 m-6 rounded-lg shadow-md transition-colors">
          <div className="p-6 border-b dark:border-gray-700">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
              {getPaginaTitulo(paginaAtiva)}
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Logado como: {usuario.nome} ({usuario.perfil})
            </p>
          </div>
          
          <div>
            {renderizarConteudo(paginaAtiva, usuario)}
          </div>
        </div>
      </div>
    </div>
  );
}

function getPaginaTitulo(pagina) {
  const titulos = {
    controle: 'Controle',
    analise: 'Análise',
    armazem: 'Armazém',
    pedidos: 'Pedidos',
    'admin-usuarios': 'Administração de Usuários',
    status: 'Status'
  };
  return titulos[pagina] || 'Dashboard';
}

function renderizarConteudo(pagina, usuario) {
  switch (pagina) {
    case 'controle':
      return <Controle usuario={usuario} />;
    case 'armazem':
      return <Armazem usuario={usuario} />;
    case 'admin-usuarios':
      return <AdminUsuarios usuario={usuario} />;
    case 'pedidos':
      return <Pedidos usuario={usuario} />;
    case 'status':
      return <Status usuario={usuario} />;
    case 'analise':
      return <Analise usuario={usuario} />;
    default:
      return <div className="p-6">Página não encontrada</div>;
  }
}