import unittest
import json
from unittest.mock import patch
from app import app


class TestLogin(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_login_sucesso(self):
        """Teste: Login com dados válidos"""
        with patch('database.verificar_usuario') as mock_verificar:
            mock_verificar.return_value = {
                'id': 1,
                'nome': '123',
                'username': '123',
                'perfil': 'gerente'
            } # O que espera receber da requisição 
            
            dados = {'username': '123', 'password': '123'} # Dados para passar ao login com o JSON
            
            response = self.app.post('/login', 
                                   data=json.dumps(dados),
                                   content_type='application/json') #Passa os dados para a rota login, com esse json 
            
            # Verificações
            self.assertEqual(response.status_code, 200) # Verifica se o status 200 do login saiu no console com a msm requisição
            resultado = json.loads(response.data) #Lê o resultado
            self.assertTrue(resultado['success'])
            self.assertEqual(resultado['message'], 'Login realizado com sucesso') #Aqui precisa ser exatamente o que sai no console quando é realizado
    
if __name__ == '__main__':
    unittest.main(verbosity=2)
