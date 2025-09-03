import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from './Login';

// TESTE 1: Verificar se o componente renderiza sem erros
test('deve renderizar o componente Login', () => {
  render(<Login onLogin={() => {}} />);
});

// TESTE 2: Verificar se os campos de input estão presentes
test('deve mostrar os campos de login e senha', () => {
  render(<Login onLogin={() => {}} />);
  expect(screen.getByPlaceholderText('LOGIN')).toBeInTheDocument();
  expect(screen.getByPlaceholderText('SENHA')).toBeInTheDocument();
});

// TESTE 3: Verificar se o botão de entrar existe
test('deve mostrar o botão ENTRAR', () => {
  render(<Login onLogin={() => {}} />);
  expect(screen.getByText('ENTRAR')).toBeInTheDocument();
});

// TESTE 4: Testar digitação nos campos
test('deve permitir digitar no campo de login', async () => {
  const user = userEvent.setup();
  render(<Login onLogin={() => {}} />);
  
  const loginField = screen.getByPlaceholderText('LOGIN');
  
  // Simula digitação
  await user.type(loginField, 'meuusuario');
    expect(loginField).toHaveValue('meuusuario');
});

// TESTE 5: Testar digitação no campo senha
test('deve permitir digitar no campo de senha', async () => {
  const user = userEvent.setup();
  render(<Login onLogin={() => {}} />);
  
  const senhaField = screen.getByPlaceholderText('SENHA');
  
  // Simula digitação
  await user.type(senhaField, 'minhasenha');
  expect(senhaField).toHaveValue('minhasenha');
});
