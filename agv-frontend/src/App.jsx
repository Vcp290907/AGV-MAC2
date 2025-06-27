import React, { useState } from "react";
import Login from "./pages/Login";

function App() {
  const [perfil, setPerfil] = useState(null);

  if (!perfil) {
    return <Login onLogin={setPerfil} />;
  }

  return (
    <div>
      <h1>Bem-vindo, {perfil}!</h1>
    </div>
  );
}

export default App;