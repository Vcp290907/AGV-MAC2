import React, { useState, useEffect } from "react";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";

function App() {
  const [usuario, setUsuario] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  const [loading, setLoading] = useState(true);

  // Carregar dados salvos no localStorage
  useEffect(() => {
    const savedUsuario = localStorage.getItem('usuario');
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
    
    if (savedUsuario) {
      try {
        setUsuario(JSON.parse(savedUsuario));
      } catch (error) {
        localStorage.removeItem('usuario');
      }
    }
    
    setDarkMode(savedDarkMode);
    if (savedDarkMode) {
      document.documentElement.classList.add('dark');
    }
    
    setLoading(false);
  }, []);

  // Função para fazer login e salvar no localStorage
  const handleLogin = (dadosUsuario) => {
    setUsuario(dadosUsuario);
    localStorage.setItem('usuario', JSON.stringify(dadosUsuario));
  };

  // Função para alternar dark mode
  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', newDarkMode.toString());
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleLogout = () => {
    setUsuario(null);
    localStorage.removeItem('usuario');
  };

  // Mostrar loading enquanto verifica localStorage
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando...</p>
        </div>
      </div>
    );
  }

  if (!usuario) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Dashboard 
      usuario={usuario}
      onLogout={handleLogout}
      darkMode={darkMode}
      toggleDarkMode={toggleDarkMode}
    />
  );
}

export default App;