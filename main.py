import csv
import networkx as nx
import matplotlib.pyplot as plt


class Atividade:
    def __init__(self, nome: str, id_atividade: int, duracao: int):
        self.nome = nome
        self.id = id_atividade
        self.duracao = duracao

        self.es = -1  # Tempo inicial mais cedo (early start)
        self.ef = -1  # Tempo final mais cedo (early finish)
        self.ls = -1  # Tempo inicial mais tarde (late start)
        self.lf = -1  # Tempo final mais tarde (late finish)

        self.precedentes = []
        self.sucessores = []

        self.folga = 0


class Projeto:
    def __init__(self):
        self.id_atual = 0
        self.atividades = {}

    def criar_atividade(self, nome: str, duracao: int = 0,
                        precedentes: list = None):
        if precedentes is None:
            precedentes = []

        atividade = Atividade(nome, self.id_atual, duracao)

        self.atividades[self.id_atual] = atividade

        for id_precedente in precedentes:
            atividade.precedentes.append(id_precedente)
            self.atividades[id_precedente].sucessores.append(self.id_atual)

        self.id_atual += 1

    def calc_tempos_cedo(self, id_atividade: int = 0, tempo_inicial: int = 0):
        atividade = self.atividades[id_atividade]

        # Uma atividade só pode ser iniciada depois que as que a precedem
        # forem concluídas, portanto, o seu tempo inicial deve estar uma
        # unidade acima do maior tempo final dentre seus precedentes
        if tempo_inicial >= atividade.es:
            if atividade.duracao:
                atividade.es = tempo_inicial + 1
                atividade.ef = tempo_inicial + atividade.duracao
            else:
                # Atividades de tempo zero não incrementam o tempo final
                atividade.es = tempo_inicial
                atividade.ef = tempo_inicial

        # Calcular os tempos para os sucessores, recursivamente
        for id_sucessor in atividade.sucessores:
            self.calc_tempos_cedo(id_sucessor, atividade.ef)

    def calc_tempos_tarde(self, id_atividade: int = None,
                          tempo_final: int = None):
        if id_atividade is None:
            # Assume-se que a atividade final é a última inserida
            id_atividade = self.id_atual - 1

        atividade = self.atividades[id_atividade]

        # Se esta for a atividade final, atribuir o tempo final a ser utilizado
        if tempo_final is None:
            tempo_final = atividade.ef

        # Recalcular os tempos mais tarde se ainda não foram atribuídos (valor
        # padrão: -1) ou se o tempo final atribuído estiver acima do tempo
        # inicial de uma atividade posterior
        if atividade.lf < 0 or atividade.lf > tempo_final:
            if atividade.duracao:
                atividade.lf = tempo_final
                atividade.ls = tempo_final - atividade.duracao + 1
                tempo_final = tempo_final - atividade.duracao
            else:
                atividade.lf = tempo_final
                atividade.ls = tempo_final
                # Para atividades de tempo zero, manter o mesmo tempo final
                # para os sucessores

        # Calcular os tempos para os precedentes, recursivamente
        for id_precedente in atividade.precedentes:
            self.calc_tempos_tarde(id_precedente, tempo_final)

    def calc_folgas(self, id_atividade: int = 0):
        atividade = self.atividades[id_atividade]

        atividade.folga = atividade.ls - atividade.es

        for id_sucessor in atividade.sucessores:
            self.calc_folgas(id_sucessor)

    def caminho_critico(self, id_atividade: int = 0,
                        caminhos: list[list[int]] = None,
                        caminho: list[int] = None):
        if caminhos is None:
            caminhos = []
        if caminho is None:
            caminho = []

        atividade = self.atividades[id_atividade]

        if not atividade.folga:
            caminho.append(id_atividade)
        else:
            return None

        # Se o vértice final for atingido, adicionar à lista de caminhos
        if not atividade.sucessores:
            caminhos.append(caminho)

        # Continuar calculando para os sucessores, cada um com um caminho
        # próprio (por isso o uso do copy)
        for id_sucessor in atividade.sucessores:
            self.caminho_critico(id_sucessor, caminhos, caminho.copy())

        return max(caminhos, key=lambda c: len(c))


projeto = Projeto()

with open('data.csv', newline='') as dados:
    leitura = csv.reader(dados, delimiter=';')
    for linha in leitura:
        nome = linha[0]
        duracao = int(linha[1])

        # Buscar os IDs dos precedentes, com base nos nomes fornecidos
        precedentes = []
        for nome_precedente in linha[2].split(sep=','):
            for atividade in projeto.atividades.values():
                if atividade.nome == nome_precedente:
                    precedentes.append(atividade.id)
                    break

        projeto.criar_atividade(nome, duracao, precedentes)

projeto.calc_tempos_cedo()
projeto.calc_tempos_tarde()
projeto.calc_folgas()

caminho_critico = projeto.caminho_critico()
caminho_critico_nomes = []
for i in range(len(caminho_critico)):
    caminho_critico_nomes.append(projeto.atividades[caminho_critico[i]].nome)

# Imprimir resumo textual do projeto
for atividade in projeto.atividades.values():
    print('Atividade:', atividade.nome)

    print('Precedentes:', end=' ')
    for id_precedente in atividade.precedentes:
        print(projeto.atividades[id_precedente].nome, end=' ')
    print()

    print('Duração:', atividade.duracao)

    # Não imprimir os tempos para atividades de duração zero
    if atividade.duracao:
        print('Tempo inicial mais cedo:', atividade.es)
        print('Tempo final mais cedo:', atividade.ef)
        print('Tempo inicial mais tarde:', atividade.ls)
        print('Tempo final mais tarde:', atividade.lf)
        print('Folga:', atividade.folga)
    print()

print('Caminho crítico:', end=' ')
for i in range(len(caminho_critico_nomes)):
    print(caminho_critico_nomes[i], end='')
    if i < len(caminho_critico) - 1:
        print(' -> ', end='')
print()

# Gerar grafo de PERT/CPM
G = nx.DiGraph()

# Adicionar nós com atributos, e arcos
critical_edges = []
for a in projeto.atividades.values():
    G.add_node(a.nome, duracao=a.duracao, es=a.es, ef=a.ef, ls=a.ls, lf=a.lf,
               folga=a.folga)
    for id_sucessor in a.sucessores:
        sucessor = projeto.atividades[id_sucessor]
        G.add_edge(a.nome, sucessor.nome)

        # Adicionar arcos que estejam no caminho crítico a uma lista especial
        if ((a.nome in caminho_critico_nomes)
                and (sucessor.nome in caminho_critico_nomes)):
            critical_edges.append((a.nome, sucessor.nome))

# Atualizar rótulos dos nós
for node in G.nodes:
    data = G.nodes[node]
    data['label'] = node

# Gerar rótulos para exibição em cada nó
# Nós de duração zero não têm tempos ou folgas mostrados
node_labels = {
    node: f'''{data['label']}  {data['duracao']}
    ES: {data['es']}  EF: {data['ef']}
    LS: {data['ls']}  LF: {data['lf']}
    F = {data['folga']}'''
    if data['duracao'] != 0 else
    f'''{data['label']}  {data['duracao']}'''
    for node, data in G.nodes(data=True)}

# Identificar o nó inicial como o de subgrau interior zero
initial_node = [node for node, degree in G.in_degree() if degree == 0][0]

pos = nx.bfs_layout(G, start=initial_node)

# Desenhar o grafo
fig, ax = plt.subplots()

options = {
    'with_labels': False,
    'node_size': 5000,
    'node_color': 'white',
    'edge_color': ["red" if edge in critical_edges else "black"
                   for edge in G.edges()],
    'width': 2,
}
nx.draw_networkx(G, pos, **options)

nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10)

# Mostrar a legenda
ax.text(0.02, 0.02,
        'ES: tempo inicial mais cedo\n'
        'EF: tempo final mais cedo\n'
        'LS: tempo inicial mais tarde\n'
        'LF: tempo final mais tarde\n'
        'F: folga',
        transform=ax.transAxes)

plt.show()
