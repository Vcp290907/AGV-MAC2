import sqlite3
import os
import hashlib

DATABASE = 'agv_system.db'

def hash_password(password):
    """Cria hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK (perfil IN ('gerente', 'funcionario')),
            ativo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de dispositivos/carrinhos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dispositivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            codigo TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'disponivel',
            bateria INTEGER DEFAULT 100,
            localizacao TEXT DEFAULT 'base',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de itens do armazém
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tag TEXT UNIQUE NOT NULL,
            categoria TEXT NOT NULL,
            imagem TEXT,
            disponivel BOOLEAN DEFAULT 1,
            posicao_x INTEGER,
            posicao_y INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de pedidos (atualizada para referenciar usuário)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            dispositivo_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (dispositivo_id) REFERENCES dispositivos (id)
        )
    ''')
    
    # Tabela de itens do pedido
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedido_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            item_id INTEGER,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
            FOREIGN KEY (item_id) REFERENCES itens (id)
        )
    ''')
    
    # Tabela de categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            cor TEXT DEFAULT '#6B7280',
            ativo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir usuários padrão
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    if cursor.fetchone()[0] == 0:
        usuarios_exemplo = [
            ('Administrador', '123', hash_password('123'), 'gerente', 1),
            ('João Silva', 'joao', hash_password('123456'), 'funcionario', 1),
            ('Maria Santos', 'maria', hash_password('123456'), 'gerente', 1),
            ('Pedro Costa', 'pedro', hash_password('123456'), 'funcionario', 1)
        ]
        
        cursor.executemany('''
            INSERT INTO usuarios (nome, username, password_hash, perfil, ativo)
            VALUES (?, ?, ?, ?, ?)
        ''', usuarios_exemplo)
        
        print("Usuários criados:")
        print("- 123/123 (gerente)")
        print("- joao/123 (funcionário)")
        print("- maria/123 (gerente)")
        print("- pedro/123 (funcionário)")
    
    # Inserir dispositivos de exemplo
    cursor.execute('SELECT COUNT(*) FROM dispositivos')
    if cursor.fetchone()[0] == 0:
        dispositivos_exemplo = [
            ('AGV-001', 'AGV001', 'disponivel', 100, 'base'),
        ]
        
        cursor.executemany('''
            INSERT INTO dispositivos (nome, codigo, status, bateria, localizacao)
            VALUES (?, ?, ?, ?, ?)
        ''', dispositivos_exemplo)
    
    # Adicionar colunas de localização à tabela itens se não existirem
    try:
        cursor.execute("PRAGMA table_info(itens)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'corredor' not in colunas:
            cursor.execute('ALTER TABLE itens ADD COLUMN corredor TEXT DEFAULT "1"')
        if 'sub_corredor' not in colunas:
            cursor.execute('ALTER TABLE itens ADD COLUMN sub_corredor TEXT DEFAULT "1"')
            
    except sqlite3.OperationalError:
        pass
    
    # Atualizar itens existentes com localização
    cursor.execute('SELECT COUNT(*) FROM itens')
    if cursor.fetchone()[0] == 0:
        items_exemplo = [
            ('Porca', '1234', 'Fixação', 'porca.png', 1, 1, 1, '1', '1'),
            ('Parafuso', '5678', 'Fixação', 'parafuso.png', 1, 2, 1, '1', '1'),
            ('Arruela', '9012', 'Fixação', 'arruela.png', 1, 3, 1, '1', '2'),
            ('Cabo USB', '3456', 'Eletrônicos', 'cabo_usb.png', 1, 1, 2, '1', '2'),
            ('Resistor', '7890', 'Eletrônicos', 'resistor.png', 1, 2, 2, '1', '3'),
            ('LED', '1111', 'Eletrônicos', 'led.png', 1, 3, 2, '1', '3')
        ]
        
        cursor.executemany('''
            INSERT INTO itens (nome, tag, categoria, imagem, disponivel, posicao_x, posicao_y, corredor, sub_corredor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', items_exemplo)
    else:
        # Atualizar itens existentes sem localização
        cursor.execute('''
            UPDATE itens 
            SET corredor = '1', sub_corredor = '1' 
            WHERE corredor IS NULL OR sub_corredor IS NULL
        ''')
    
    # Inserir categorias padrão
    cursor.execute('SELECT COUNT(*) FROM categorias')
    if cursor.fetchone()[0] == 0:
        categorias_exemplo = [
            ('Fixação', '#EF4444'),
            ('Eletrônicos', '#3B82F6'),
            ('Ferramentas', '#F59E0B'),
            ('Diversos', '#6B7280')
        ]
        
        cursor.executemany('''
            INSERT INTO categorias (nome, cor)
            VALUES (?, ?)
        ''', categorias_exemplo)
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado!")

def get_db_connection():
    """Retorna uma conexão com o banco"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def verificar_usuario(username, password):
    """Verifica credenciais do usuário"""
    conn = get_db_connection()
    password_hash = hash_password(password)
    
    usuario = conn.execute('''
        SELECT id, nome, username, perfil, ativo
        FROM usuarios 
        WHERE username = ? AND password_hash = ? AND ativo = 1
    ''', (username, password_hash)).fetchone()
    
    conn.close()
    
    if usuario:
        return dict(usuario)
    return None