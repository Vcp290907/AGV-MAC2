import React, { useState } from "react";

export default function Login({ onLogin }) {
  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro("");
    try {
      const resp = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario, senha }),
      });
      const data = await resp.json();
      if (data.success) {
        onLogin(data.perfil);
      } else {
        setErro(data.message || "Login inválido");
      }
    } catch {
      setErro("Erro ao conectar com o servidor");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-400 to-red-400 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo e Título */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-6">
            <span className="bg-red-500 text-white px-6 py-3 rounded-lg text-3xl font-bold mr-3">
              MAC
            </span>
            <span className="text-black text-5xl font-bold">
              DASHBOARD
            </span>
          </div>
      </div>

        {/* Formulário */}
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Erro */}
            {erro && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg text-sm">
                {erro}
              </div>
            )}

            {/* Campo Login */}
            <div>
              <input
                className="w-full px-4 py-3 bg-gray-300 rounded-lg placeholder-gray-600 text-gray-800 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-colors"
                type="text"
                placeholder="LOGIN"
                value={usuario}
                onChange={(e) => setUsuario(e.target.value)}
                required
              />
            </div>

            {/* Campo Senha */}
            <div>
              <input
                className="w-full px-4 py-3 bg-gray-300 rounded-lg placeholder-gray-600 text-gray-800 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-colors"
                type="password"
                placeholder="SENHA"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
              />
            </div>

            {/* Botão Entrar */}
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-teal-500 to-red-500 text-white py-3 rounded-lg font-bold text-lg hover:from-teal-600 hover:to-red-600 transform hover:scale-[1.02] transition-all duration-200 shadow-lg"
            >
              ENTRAR
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}