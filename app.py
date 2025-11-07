import os
import sqlite3
# --- IMPORTAÇÕES DE FUSO HORÁRIO CORRIGIDAS ---
from datetime import datetime
import pytz # Usaremos pytz diretamente, é mais confiável
# --- FIM DA CORREÇÃO ---

from flask import Flask, render_template, request, redirect, url_for, session, flash

# Configuração do App Flask
app = Flask(__name__)
# Chave secreta necessária para 'session' e 'flash'
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_forte_12345'
# Nome do banco de dados
DATABASE_NAME = 'saep_db.db'

# --- Funções Auxiliares de Banco de Dados ---

def get_db_connection():
    """Cria uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return conn

def init_db():
    """Executa o script SQL para inicializar o banco de dados."""
    if not os.path.exists(DATABASE_NAME):
        print(f"Criando banco de dados '{DATABASE_NAME}'...")
        conn = get_db_connection()
        # Garante que o encoding esteja correto, especialmente no Windows
        with open('database.sql', 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("Banco de dados inicializado com sucesso.")

# Decorator para verificar se o usuário está logado
def login_required(f):
    """Garante que o usuário esteja logado antes de acessar uma rota."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas da Aplicação ---

# ENTREGA 4: Interface de Autenticação (Login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Usuario WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        conn.close()
        
        if user:
            # Salva informações do usuário na sessão
            session['user_id'] = user['id']
            session['user_name'] = user['nome_completo']
            return redirect(url_for('index'))
        else:
            # Exibe mensagem clara em caso de falha
            flash('Usuário ou senha inválidos.', 'danger')
            # Redireciona de volta ao login
            return redirect(url_for('login'))
            
    return render_template('login.html')

# Rota de Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))


# ENTREGA 5: Interface Principal do Sistema
@app.route('/')
@login_required
def index():
    # Exibe nome do usuário logado (passado pelo layout.html)
    # Permite acesso às telas
    return render_template('index.html')


# ENTREGA 6: Interface de Cadastro de Produto (CRUD)
@app.route('/produtos', methods=['GET'])
@login_required
def produtos():
    search_query = request.args.get('search', '') # Campo de busca
    conn = get_db_connection()
    
    if search_query:
        query = 'SELECT * FROM Produto WHERE nome LIKE ? OR descricao LIKE ? OR variacao LIKE ?'
        produtos = conn.execute(query, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        # Lista produtos cadastrados
        produtos = conn.execute('SELECT * FROM Produto').fetchall()
        
    conn.close()
    return render_template('produtos.html', produtos=produtos, search_query=search_query)

# Inserir Produto
@app.route('/produtos/novo', methods=['POST'])
@login_required
def produto_novo():
    # Validação (embora a principal seja no frontend/HTML)
    nome = request.form.get('nome')
    variacao = request.form.get('variacao')
    
    if not nome or not variacao:
        flash('Nome e Variação são campos obrigatórios.', 'danger')
        return redirect(url_for('produtos'))

    descricao = request.form.get('descricao')
    estoque_minimo = request.form.get('estoque_minimo', 1, type=int)

    conn = get_db_connection()
    conn.execute('INSERT INTO Produto (nome, descricao, variacao, estoque_minimo, quantidade_atual) VALUES (?, ?, ?, ?, 0)',
                 (nome, descricao, variacao, estoque_minimo))
    conn.commit()
    conn.close()
    
    flash('Produto cadastrado com sucesso!', 'success')
    return redirect(url_for('produtos'))

# Editar Produto
@app.route('/produtos/editar/<int:id>', methods=['POST'])
@login_required
def produto_editar(id):
    nome = request.form.get('nome')
    variacao = request.form.get('variacao')

    if not nome or not variacao:
        flash('Nome e Variação são campos obrigatórios.', 'danger')
        return redirect(url_for('produtos'))

    descricao = request.form.get('descricao')
    estoque_minimo = request.form.get('estoque_minimo', 1, type=int)

    conn = get_db_connection()
    conn.execute('UPDATE Produto SET nome = ?, descricao = ?, variacao = ?, estoque_minimo = ? WHERE id = ?',
                 (nome, descricao, variacao, estoque_minimo, id))
    conn.commit()
    conn.close()
    
    flash('Produto atualizado com sucesso!', 'success')
    return redirect(url_for('produtos'))

# Excluir Produto
@app.route('/produtos/excluir/<int:id>', methods=['POST'])
@login_required
def produto_excluir(id):
    conn = get_db_connection()
    # Verifica se há movimentações (para integrencial referencial)
    movs = conn.execute('SELECT COUNT(*) FROM Movimentacao WHERE produto_id = ?', (id,)).fetchone()[0]
    
    if movs > 0:
        flash('Não é possível excluir: Produto possui histórico de movimentação.', 'danger')
    else:
        conn.execute('DELETE FROM Produto WHERE id = ?', (id,))
        conn.commit()
        flash('Produto excluído com sucesso!', 'success')
        
    conn.close()
    return redirect(url_for('produtos'))


# ENTREGA 7: Interface de Gestão de Estoque
@app.route('/estoque', methods=['GET'])
@login_required
def estoque():
    conn = get_db_connection()
    # Lista produtos em ordem alfabética
    produtos = conn.execute('SELECT * FROM Produto ORDER BY nome ASC').fetchall()
    conn.close()
    
    # Lógica de alerta passada para o template
    return render_template('estoque.html', produtos=produtos)

# Movimentar Estoque (Entrada ou Saída)
@app.route('/estoque/movimentar', methods=['POST'])
@login_required
def estoque_movimentar():
    try:
        produto_id = request.form.get('produto_id', type=int)
        tipo = request.form.get('tipo')
        quantidade = request.form.get('quantidade', type=int)
        usuario_id = session['user_id']
        
        if not produto_id or not tipo or not quantidade or quantidade <= 0:
            flash('Dados da movimentação inválidos.', 'danger')
            return redirect(url_for('estoque'))

        conn = get_db_connection()
        produto = conn.execute('SELECT * FROM Produto WHERE id = ?', (produto_id,)).fetchone()

        if tipo == 'Entrada':
            nova_qtd = produto['quantidade_atual'] + quantidade
        elif tipo == 'Saida': # Corrigido sem acento
            nova_qtd = produto['quantidade_atual'] - quantidade
            if nova_qtd < 0:
                flash(f"Operação falhou: Estoque de '{produto['nome']}' não pode ficar negativo.", 'danger')
                conn.close()
                return redirect(url_for('estoque'))
        else:
            flash('Tipo de operação inválido.', 'danger')
            conn.close()
            return redirect(url_for('estoque'))
            
        # --- INÍCIO DA CORREÇÃO DE FORMATAÇÃO DE DATA ---
        
        # 1. Define o fuso horário de Brasília (America/Sao_Paulo)
        fuso_horario_brt = pytz.timezone("America/Sao_Paulo")
        
        # 2. Pega a data e hora atuais NESSE fuso
        data_hora_obj = datetime.now(fuso_horario_brt)
        
        # 3. Formata a data como texto, sem microssegundos e com a sigla do fuso
        #    %Y-%m-%d -> 2025-11-03
        #    %H:%M:%S -> 21:05:30
        #    %Z        -> BRT (ou BRST dependendo da época)
        data_hora_formatada = data_hora_obj.strftime('%Y-%m-%d %H:%M:%S %Z')

        # --- FIM DA CORREÇÃO ---


        # Inicia uma transação
        conn.execute('BEGIN TRANSACTION')
        try:
            # 1. Atualiza o estoque do produto
            conn.execute('UPDATE Produto SET quantidade_atual = ? WHERE id = ?', (nova_qtd, produto_id))
            
            # 2. Registra no histórico, passando a data_hora_formatada explicitamente
            conn.execute(
                'INSERT INTO Movimentacao (produto_id, usuario_id, tipo, quantidade, data_hora) VALUES (?, ?, ?, ?, ?)',
                (produto_id, usuario_id, tipo, quantidade, data_hora_formatada) # Passando a string formatada
            )
            
            conn.commit() # Confirma a transação
            flash(f"{tipo} de {quantidade} unidade(s) de '{produto['nome']}' registrada.", 'success')
        except Exception as e:
            conn.rollback() # Desfaz em caso de erro
            flash(f'Erro na transação: {e}', 'danger')

        conn.close()
        
    except Exception as e:
        flash(f'Erro ao processar movimentação: {e}', 'danger')
        
    return redirect(url_for('estoque'))


# --- ROTA DE HISTÓRICO ADICIONADA (Para RF009 e RF011) ---

@app.route('/historico')
@login_required
def historico():
    conn = get_db_connection()
    # Query que junta as 3 tabelas para um histórico completo
    # (Quem, O quê, Quando, Quanto)
    query = """
    SELECT 
        m.data_hora,
        p.nome as produto_nome,
        p.variacao,
        u.nome_completo as usuario_nome,
        m.tipo,
        m.quantidade
    FROM 
        Movimentacao m
    JOIN 
        Produto p ON m.produto_id = p.id
    JOIN 
        Usuario u ON m.usuario_id = u.id
    ORDER BY 
        m.data_hora DESC
    """
    movimentacoes = conn.execute(query).fetchall()
    conn.close()
    
    return render_template('historico.html', movimentacoes=movimentacoes)


# --- Inicialização ---
if __name__ == '__main__':
    init_db() # Garante que o DB exista antes de rodar
    app.run(debug=True, port=5000)