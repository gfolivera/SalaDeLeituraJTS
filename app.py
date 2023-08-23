import mysql.connector
from mysqlx import IntegrityError
import streamlit as st
import pandas as pd
import datetime

cnx = mysql.connector.connect(user='root', password='root',
                              host='127.0.0.1',
                              database='saladeleiturajts')

cursor = cnx.cursor()


def do_query():
    cursor.execute("SELECT * FROM livros WHERE id < 50")
    myresult = cursor.fetchall()
    for x in myresult:
        print(x)


def query_assuntos():
    cursor.execute("SELECT * FROM assunto ORDER BY nome")
    myresult = cursor.fetchall()
    assuntos_nomes = []
    assuntos_list = []
    for x in myresult:
        assuntos_nomes.append(x[1])
        assuntos_list.append(x)
    return assuntos_nomes, assuntos_list


# cnx.close()

def main():
    st.title("SALA DE LEITURA JTS 2.0")
    assuntos_nomes, assuntos_list = query_assuntos()

    # OPÇÕES DE OPERAÇÃO
    option = st.sidebar.selectbox("Select an operation:", ('Adicionar', 'Buscar', 'Empréstimo', 'Delete'))
    if option == 'Adicionar':

        add_options = st.selectbox("Escolha um tipo de adição:", ("Livro", "Aluno(s)"))

        if add_options == "Livro":
            isbn_livro = ""
            st.subheader("Adicionar um Livro")
            nome_livro = st.text_input("Nome do livro")
            autor_livro = st.text_input("Autor do livro")
            # selecionador de assuntos. inclui um checkbox para caso não tenha o assunto desejado.
            # o check cria um text input para incluir o assunto, e atualiza o multiselect.
            assunto_placeholder = st.empty()
            with assunto_placeholder.container():
                assuntos_multiselect = st.multiselect("Assuntos:", assuntos_nomes,
                                                      placeholder="Caso não encontre, marque a caixa abaixo")
            assunto_ausente = st.checkbox("Assunto não está listado", value=False)
            # checkbox marcado, o assunto não foi encontrado
            if assunto_ausente:
                assunto_input = st.text_input("Digite o assunto a ser incluído na lista")
                if st.button("Adicionar Assunto"):
                    if assunto_input == "":
                        st.warning('Assunto vazio não pode ser incluído.', icon="⚠️")
                    else:
                        assunto_insert = [assunto_input]
                        sql = "INSERT INTO assunto(nome) VALUES(%s)"
                        cursor.execute(sql, assunto_insert)
                        cnx.commit()
                        cursor.execute("SELECT max(id) FROM assunto")
                        myresult = cursor.fetchall()
                        novo_id = myresult[0][0]
                        st.success(f"Novo assunto incluído com sucesso. id: {novo_id}")
                        assuntos_nomes, assuntos_list = query_assuntos()
                        assunto_placeholder.empty()
                        with assunto_placeholder.container():
                            assuntos_multiselect = st.multiselect("Assuntos:", assuntos_nomes,
                                                                  placeholder="Caso não encontre, marque a caixa abaixo")

            isbn_check = st.checkbox("Sem ISBN", value=True)
            if not isbn_check:
                isbn_livro = st.text_input("ISBN do livro", max_chars=14)
            edicao_livro = st.number_input("Edição do livro", min_value=1, step=1, format="%.0d")
            # USUÁRIO clicou para adicionar livro
            if st.button("Adicionar Livro"):
                check = True
                if isbn_check:
                    isbn_livro = "Sem ISBN"
                if isbn_livro == "":
                    st.warning('ISBN deve ser preenchido. Caso não haja, marque como "Sem Isbn"', icon="⚠️")
                    check = False
                if check:
                    sql = "INSERT INTO livros(NOME, AUTOR, isbn, EDICAO) VALUES(%s,%s,%s,%s)"
                    values = (nome_livro, autor_livro, isbn_livro, edicao_livro)
                    cursor.execute(sql, values)
                    cnx.commit()
                    cursor.execute("SELECT max(id) FROM livros")
                    myresult = cursor.fetchall()
                    novo_id = myresult[0][0]
                    # percorrer lista de assuntos procurando id dos assuntos selecionados
                    for assunto in assuntos_multiselect:
                        for i in range(len(assuntos_list)):
                            if assuntos_list[i][1] == assunto:
                                assuntos_val = (novo_id, assuntos_list[i][0])
                                print(assuntos_val)
                                sql = "INSERT INTO assunto_tratado(id_livro, id_assunto) VALUES(%s,%s)"
                                cursor.execute(sql, assuntos_val)
                                cnx.commit()
                                break
                    st.success(f"Livro registrado. ID: {novo_id}")
                    st.write("Aperte o botão novamente para registrar o mesmo livro mais uma vez")

        if add_options == "Aluno(s)":
            filepath = st.file_uploader("Arquivo CSV", accept_multiple_files=False)

            if st.button("Adicionar"):

                df = pd.read_csv(filepath, sep=';', skiprows=1)
                st.write(df)
                insert_list = []
                str_nomes = ""
                ja_cadastrados = []

                def csv_iterrows():

                    for col, row in df.iterrows():
                        # 3-nome; 4-RA; 5-dig RA; 6-sp; 7-nascimento
                        data_nasc_aux = (row[7]).split("/")
                        # formata data de nascimento para o formato do MySQL aaaa-mm-dd
                        data_nasc = f'{data_nasc_aux[2]}-{data_nasc_aux[1]}-{data_nasc_aux[0]}'
                        insert_list.append([row[3], row[4], data_nasc])

                def query_select():
                    # colocar try exception IntegrityError - RA já cadastrado
                    print(len(insert_list))
                    ja_cadastrados_bool = False
                    for i in range(len(insert_list)):
                        try:
                            cursor.execute("INSERT INTO alunos(NOME, RA, data_nascimento) VALUES(%s,%s,%s)",
                                           (insert_list[i][0], insert_list[i][1], insert_list[i][2]))
                            cnx.commit()
                        except mysql.connector.errors.IntegrityError:
                            ja_cadastrados.append(insert_list[i][0])
                            ja_cadastrados_bool = True
                    if ja_cadastrados_bool:
                        nomes = ", ".join(ja_cadastrados)
                        st.write(f'Aluno(s) já cadastrado(s): {nomes}')

                csv_iterrows()
                query_select()

    elif option == 'Buscar':
        # INCLUIR MAIS OPÇÕES DE BUSCA, E ROTULOS PARA AS COLUNAS
        options_tuple = ("Livros", "Alunos")
        busca = st.selectbox("Tipo de Busca", options_tuple)
        st.subheader(f"Buscar {busca}")
        st.write("Busca por")
        checks_container = st.container()

        if busca == "Livros":
            with checks_container:
                col_1, col_2, col_3 = st.columns(3)
                with col_1:
                    check_id_busca = st.checkbox("Id", value=False)
                with col_2:
                    check_nome_livro_busca = st.checkbox("Nome", value=False)
                with col_3:
                    check_autor_busca = st.checkbox("Autor", value=False)

            if check_id_busca:
                id_busca = st.number_input("ID do livro", min_value=0, step=1, format="%.0d")
            if check_nome_livro_busca:
                nome_livro_busca = st.text_input("Nome do Livro", max_chars=100)
            if check_autor_busca:
                autor_busca = st.text_input("Autor(es)", max_chars=60)
            botao_buscar = st.button("Buscar")
            tabela = st.table()
            if botao_buscar:
                all_checks = True
                param_list = []

                if check_id_busca:
                    if id_busca == 0:
                        st.warning("id deve ser preenchido ou desmarcado.")
                        all_checks = False
                    else:
                        param_list.append(f'id = {id_busca}')

                if check_nome_livro_busca:
                    if nome_livro_busca == "":
                        st.warning("nome deve ser preenchido ou desmarcado.")
                        all_checks = False
                    else:
                        param_list.append(f"nome LIKE '%{nome_livro_busca}%'")

                if check_autor_busca:
                    if autor_busca == "":
                        st.warning("autor deve ser preenchido ou desmarcado.")
                        all_checks = False
                    else:
                        param_list.append(f"autor LIKE '%{autor_busca}%'")

                parametros = len(param_list)
                if parametros > 1:
                    param_list.insert(1, " AND ")
                    if parametros == 3:
                        param_list.insert(3, " AND ")

                if all_checks:
                    sql = "SELECT * FROM livros WHERE "
                    for item in param_list:
                        sql = sql + item
                    # sql = "SELECT * FROM livros WHERE id = %s"
                    # id_query = [id_busca]
                    cursor.execute(sql)

                    # cursor.execute(sql, id_query)
                    myresult = cursor.fetchall()
                    df = pd.DataFrame(myresult,
                                      columns=['id', 'Nome do Livro', 'Autor', 'ISBN', 'Edição', 'Disponível'])
                    tabela.table(df)

        else:

            with checks_container:
                col_1, col_2 = st.columns(2)
                with col_1:
                    check_ra_read = st.checkbox("RA", value=False)
                with col_2:
                    check_name_read = st.checkbox("Nome", value=False)

                if check_ra_read:
                    ra_read = st.text_input("RA", max_chars=9)
                    df = pd.DataFrame()
                    ra_read_button = st.button("Buscar RA")
                    if ra_read_button:
                        sql = f"SELECT ra, nome, data_nascimento FROM  alunos WHERE ra = '{ra_read}'"
                        cursor.execute(sql)
                        myresult = cursor.fetchall()
                        df = pd.DataFrame(myresult,
                                          columns=['RA', 'Nome do Aluno', 'Data de Nascimento'])
                    tabela = st.table()
                    tabela.table(df)

                if check_name_read:
                    name_read = st.text_input("Nome", max_chars=9)
                    df = pd.DataFrame()
                    ra_read_button = st.button("Buscar RA")
                    if ra_read_button:
                        sql = f"SELECT ra, nome, data_nascimento FROM  alunos WHERE nome LIKE '%{name_read}%'"
                        cursor.execute(sql)
                        myresult = cursor.fetchall()
                        df = pd.DataFrame(myresult,
                                          columns=['RA', 'Nome do Aluno', 'Data de Nascimento'])
                    tabela = st.table()
                    tabela.table(df)

    elif option == 'Empréstimo':
        st.subheader("Empréstimos")
        emprestimo_opcoes = st.selectbox("Operação:", ("Adicionar", "Baixa", "Busca"))

        if 'clicked' not in st.session_state:
            st.session_state.clicked = {1: False, 2: False, 3: False, 4: False, 5: 'Check aluno', 6: 'Check livro',
                                        # adicionar empréstimo
                                        7: False, 8: False}
            st.session_state.disable = True

        # função que atualiza o session_state para que os radio buttons não sumam depois do clique
        def clicked(button):
            if button == 5:
                st.session_state.clicked[1] = False
            elif button == 6:
                st.session_state.clicked[4] = False
            else:
                st.session_state.clicked[button] = True
                if st.session_state.clicked[1] and st.session_state.clicked[3]:
                    st.session_state.disable = False

        if emprestimo_opcoes == 'Adicionar':

            col_1, col_2 = st.columns(2)
            aluno_escolhido, livro_escolhido = "", ""
            with col_1:
                aluno_por_nome = st.checkbox("Aluno por nome", on_change=clicked, args=[5], value=True)
                if aluno_por_nome:
                    nome_aluno = st.text_input("Nome do aluno")
                    st.button("Buscar Aluno", on_click=clicked, args=[1])
                    if st.session_state.clicked[1]:
                        if nome_aluno == "":
                            st.warning("nome deve ser preenchido ou desmarcado.")
                            all_checks = False
                        else:
                            sql = f"SELECT NOME, data_nascimento, RA FROM ALUNOS WHERE NOME LIKE '%{nome_aluno}%'"
                            cursor.execute(sql)
                            myresult = cursor.fetchall()
                            alunos_buscados = []
                            for result in myresult:
                                add_alunos_buscados = f'{result[0]} - {result[1].strftime("%d/%m/%y")} - {result[2]}'
                                alunos_buscados.append(add_alunos_buscados)
                        aluno_escolhido = st.radio("Selecione um aluno(Nome - Nascimento - RA):",
                                                   options=alunos_buscados, on_change=clicked, args=[2])

            with col_2:
                livro_por_id = st.checkbox("Livro por ID", on_change=clicked, args=[6], value=True)
                if livro_por_id:
                    livro_id = st.number_input("ID do livro", min_value=1, step=1)
                    st.button("Buscar Livro", on_click=clicked, args=[3])
                    if st.session_state.clicked[3]:
                        sql = f"SELECT ID, nome, autor FROM livros WHERE ID = {livro_id}"
                        cursor.execute(sql)
                        myresult = cursor.fetchall()
                        livros_buscados = []
                        for result in myresult:
                            add_livros_buscados = f'{result[0]} - {result[1]} - {result[2]}'
                            livros_buscados.append(add_livros_buscados)
                        livro_escolhido = st.radio("Selecione um livro(ID - Nome - Autor):", options=livros_buscados,
                                                   on_change=clicked, args=[4])

            botao_adicionar = st.button("Adicionar", disabled=st.session_state.disable)
            if st.session_state.clicked[1] and st.session_state.clicked[3]:

                ra_emprestimo = aluno_escolhido.split(" - ")
                id_emprestimo = livro_escolhido.split(" - ")
                if botao_adicionar:
                    agora = datetime.datetime.now()
                    data_emprestimo = agora.strftime('%y-%m-%d %H:%M:%S')
                    # dia e ano invertidas no print success para facilitar leitura
                    st.success(
                        f'RA aluno: {ra_emprestimo[2]}, livro: {id_emprestimo[0]}, data de inclusão:{agora.strftime("%d-%m-%y %H:%M:%S")}')
                    sql = f"INSERT INTO emprestimos(ra_aluno, id_livro, data_emprestimo) VALUES({ra_emprestimo[2]},{id_emprestimo[0]},'{data_emprestimo}')"
                    cursor.execute(sql)
                    cnx.commit()

        if emprestimo_opcoes == 'Baixa':

            emprestimo_escolhido = ""
            nome_aluno = st.text_input("Nome do aluno")
            st.button("Buscar Aluno", on_click=clicked, args=[7])
            if st.session_state.clicked[7]:
                if nome_aluno == "":
                    st.warning("nome deve ser preenchido ou desmarcado.")
                    all_checks = False
                else:
                    sql = f'''SELECT e.id_emprestimo AS 'ID Emp', e.data_emprestimo AS 'Data Emp',
                            a.nome AS 'Nome Aluno',
                            a.data_nascimento,
                            l.nome AS 'Nome livro',
                            l.id as 'ID livro'
                            FROM emprestimos as e
                            INNER JOIN livros as l ON e.id_livro = l.ID
                            INNER JOIN alunos as a on a.RA = e.ra_aluno
                            WHERE a.nome LIKE '%{nome_aluno}%' AND e.data_devolucao IS NULL
                            ORDER BY a.nome;'''
                    cursor.execute(sql)
                    myresult = cursor.fetchall()
                    emprestimos_buscados = []
                    for result in myresult:
                        add_empr_buscado = f'{result[0]} - {result[1].strftime("%d/%m/%y %H:%M:%S")} - {result[2]} - {result[3].strftime("%d/%m/%y")} - {result[4]} - {result[5]}'
                        emprestimos_buscados.append(add_empr_buscado)
                    emprestimo_escolhido = st.radio(
                        "Selecione um empréstimo(ID - Empréstimo -  Aluno - Nascimento - Livro - Id Livro):",
                        options=emprestimos_buscados, on_change=clicked, args=[8])
                    give_back_button = st.button("Efetuar Devolução")
                    if give_back_button:
                        pick_id = ""
                        pick_id = emprestimo_escolhido.split(" - ")
                        agora = datetime.datetime.now()
                        give_back_date = agora.strftime('%y-%m-%d %H:%M:%S')
                        sql = f"UPDATE emprestimos SET data_devolucao = '{give_back_date}' WHERE id_emprestimo = {pick_id[0]};"
                        try:
                            cursor.execute(sql)
                            st.success("Livro devolvido com sucesso.")
                        except Exception:
                            if Exception == IntegrityError:
                                st.error(f"Erro na execução do comando ao banco de dados. {Exception}")
                            else:
                                st.error(Exception)

        if emprestimo_opcoes == 'Busca':
            pass

    elif option == 'Delete':
        st.subheader("Read a record")


if __name__ == "__main__":
    main()
