-- Limpa as tabelas se elas já existirem (para testes)
DROP TABLE IF EXISTS Movimentacao;
DROP TABLE IF EXISTS Produto;
DROP TABLE IF EXISTS Usuario;

-- Tabela de Usuários (Para Login e Rastreabilidade)
CREATE TABLE Usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nome_completo TEXT NOT NULL
);

-- Tabela de Produtos
CREATE TABLE Produto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    variacao TEXT NOT NULL, -- Ex: "16GB RAM, 512GB SSD" ou "128GB, Preto"
    quantidade_atual INTEGER NOT NULL DEFAULT 0,
    estoque_minimo INTEGER NOT NULL DEFAULT 5
);

-- Tabela de Histórico de Movimentações
CREATE TABLE Movimentacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('Entrada', 'Saida')),
    quantidade INTEGER NOT NULL,
    data_hora DATETIME NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES Produto(id),
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id)
);

--- POPULAÇÃO DAS TABELAS (TEMA: ELETRÔNICOS) ---

-- Usuários (Senha '123' - Em produção, use HASH!)
INSERT INTO Usuario (username, password, nome_completo) VALUES
('admin', '123', 'Administrador do Sistema'),
('almox', '123', 'Funcionario Almoxarifado'),
('gerente', '123', 'Gerente de Produção');

-- Produtos (Eletrônicos)
INSERT INTO Produto (nome, descricao, variacao, quantidade_atual, estoque_minimo) VALUES
('Notebook', 'Notebook 15.6" Intel i7', '16GB RAM, 512GB SSD, Prata', 15, 5),
('Smartphone', 'Smartphone 6.7" Tela OLED', '128GB, Preto, 5G', 40, 10),
('Smart TV', 'Smart TV 55" 4K', 'LED, Wi-Fi, Tizen OS', 20, 8),
('Monitor LED', 'Monitor Widescreen 24"', 'Full HD, HDMI/VGA, 75Hz', 30, 5);