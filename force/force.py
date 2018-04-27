"""This script file generate a random feeder with medium and 
low voltage nodes, write the graph to a networkx graph object
then write the graph to a json file named force.json with some
 grid informations. This file is loaded and used to create 
 mygrid objects and can be used to visualize the grid in a html
 page. For this just open the force.html in a web browser. 
"""

#    Copyright (C) 2018 by
#    Lucas S Melo <lucassmelo@dee.ufc.br>
#    All rights reserved.
#    BSD license.

__author__ = """Lucas S Melo <lucassmelo@dee.ufc.br>"""
import json
import networkx as nx
from networkx.readwrite import json_graph
import random
import numpy as np
from tqdm import tqdm

 # mygrid imports
from mygrid.grid import GridElements, ExternalGrid, Section, LoadNode
from mygrid.grid import Conductor, Switch, TransformerModel, LineModel
from mygrid.util import p2r, r2p
from mygrid.power_flow.backward_forward_sweep_3p import calc_power_flow


def _search_tree_n_recursive(node, stack, prob, max_nodes, visit, tree):
    """Este metodo tem por objetivo gerar uma árvore de grafo
    aleatoria sem utilizar um processo recursivo

    node: no a ser analisado.
    stack: pilha que indica a posicao atual na arvore de grafo.
    prob: probabilidade para criacao de novos nós.
    max_nodes: numero maximo de nós na árvore de grafo.
    visit: nós já visitados.
    tree: dicionário que representa a árvore de grafo, em que
          as chaves representam os nós e os valores são uma lista
          com todos os vizinhos do nó.
    """

    # se o nó atial não foi visitado ele é acrescentado na
    # lista de nós não visitados 
    if node not in visit:
        visit.append(node)
        # se o nó não está presente no dicionário que representa
        # a árvore de grafo ele é acrecentado
        if node not in tree.keys():
            tree[node] = list()

    # verifica se a árvore de grafo já tem a quantidade máxima
    # admissível de nós
    if len(visit) < max_nodes:

        # calcula um número aleatorio e compara a uma probabilidade
        # pré-estabelecida para que um novo nó seja criado.
        # Também limita o numero máximo de arestas de cada nó em 4 arestas
        if random.random() < prob and len(tree[node]) < 4:
            stack.append(node)
            new_node = max(visit) + 1
            tree[node].append(new_node)
            tree[new_node] = [node]
            return (new_node, stack, max_nodes, visit, tree)
        # esta condição foi acrescentada para melhorar o espalhamento
        # da verificação nos nós da árvore de grafo
        elif len(tree[node]) == 4:
            new_node = random.sample(tree[node], 1)[0]
            if new_node in stack:
                stack.pop()
            else:
                stack.append(new_node)
            return (new_node, stack, max_nodes, visit, tree)
        # caso não seja gerado um novo nó a partir do nó atual
        # e o número de vizinhos seja maior que 4 então volta-se
        # um nível na pilha do grafo
        else:
            if stack != []:
                new_node = stack.pop()
            else:
                new_node = node
            
            if new_node not in tree[node]:
                tree[node].append(new_node)
            
            if node not in tree[new_node]:
                tree[new_node].append(node)
            return (new_node, stack, max_nodes, visit, tree)
    
    # caso o número máximo de nós estabelecidos para o grafo seja atingido
    # então encerra-se o processo de busca
    elif len(visit) == max_nodes:
        return (new_node, stack, max_nodes, visit, tree)

def generate_tree_graph(node, tree, max_nodes, prob):
    """Este método tem como objetivo realizar as chamadas pelo método
    _serach_tree_n_recursive uma vez que este é resultado de uma adaptação
    do método _search_tree para retirar a recursividade. 
    """
    stack = []
    visit = []
    nodes_count = dict()
    prob_ = prob

    # loço principal, realiza as chamadas ao método _search_tree_n_recursive
    # enquanto o número de nós da árvore gerada for inferior ao número máximo
    # pré-estabelecido.
    while len(tree.keys()) < max_nodes:
        data = _search_tree_n_recursive(node, stack, prob_, max_nodes, visit, tree)
        node = data[0]
        stack = data[1]
        max_nodes = data[2]
        visit = data[3]
        tree = data[4]

        # lógica para atualizacao do valor de probabilidade
        # esta lógica é realizada para impedir que o estabelecimento
        # de uma probabilidade muito baixa cause demora no processo
        # de busca para gerar a árvore de grafo.
        
        # adiciona o nó atual no dicionário de verificação
        if node not in nodes_count.keys():
            nodes_count[node] = 0
        # caso o nó seja reincidente, acrescenta-se 1 à contagem
        else:
            nodes_count[node] += 1

        # loop para verificação de incidencias
        for i, j in nodes_count.items():
            # caso o nó tenha uma incidencia de 20
            # a probabilidade de geração é aumentada
            if j >= 20:
                nodes_count[i] = 0
                prob_ += 0.02
                if prob_ >= 1:
                    prob_ = prob
                break

    return tree

def _search_tree(node, stack, prob, max_nodes, visit, tree):
    """Este metodo tem por objetivo gerar uma árvore de grafo
    aleatoria utilizando um processo recursivo

    node: no a ser analisado.
    stack: pilha que indica a posicao atual na arvore de grafo.
    prob: probabilidade para criacao de novos nós.
    max_nodes: numero maximo de nós na árvore de grafo.
    visit: nós já visitados.
    tree: dicionário que representa a árvore de grafo, em que
          as chaves representam os nós e os valores são uma lista
          com todos os vizinhos do nó.
    """

    # verifica se o no atual ja foi visitado, caso este ainda não
    # tenha sido visitado ele é incorporado à árvore de grafo.
    if node not in visit:
        visit.append(node)
        if node not in tree.keys():
            tree[node] = list()

    # verifica se a árvore de grafo já tem a quantidade máxima
    # admissível de nós
    if len(visit) < max_nodes:

        # calcula um número aleatorio e compara a uma probabilidade
        # pré-estabelecida para que um novo nó seja criado.
        # Também limita o numero máximo de arestas de cada nó em 4 arestas
        if random.random() < prob and len(tree[node]) < 4:
            stack.append(node)
            new_node = max(visit) + 1
            tree[node].append(new_node)
            tree[new_node] = [node]
            return _search_tree(node=new_node, stack=stack, prob=prob, max_nodes=max_nodes, visit=visit, tree=tree)
        else:
            if stack != []:
                new_node = stack.pop()
            else:
                new_node = node
            if new_node not in tree[node]:
                tree[node].append(new_node)
            if node not in tree[new_node]:
                tree[new_node].append(node)
            return _search_tree(node=new_node, stack=stack, prob=prob, max_nodes=max_nodes, visit=visit, tree=tree)
                
    elif len(visit) == max_nodes:
        return tree

def generate_grid(nodes_mv, nodes_lv):
    """Este método tem por objetivo montar a árvore de grafo que irá
    representar a rede elétrica de média e de baixa tensão, neste método
    é chamado o método generate_tree_graph para gerar o alimentador de média
    e também cada um de seus dos ramos de baixa tensão, de acordo com os
    parâmetros passados nodes_mv e nodes_lv.

    Neste método também é gerado um objeto graph do módulo python de análise
    de grafos nxnetwork e a partir dele armazenado criado um dicionário com
    outras especificações para que possa ser escrito o arquivo force.json com
    todos os detalhes necessários para montagem da rede elétrica com o módulo
    My_Grid.
    """


    # gera o grafo da rede de média tensão
    prob_ = 0.6
    max_nodes_ = nodes_mv
    tree_ = {0: [1], 1: [0, 2], 2: [1]}
    t = generate_tree_graph(node=2, tree=tree_, max_nodes=max_nodes_, prob=prob_)
    graph = nx.Graph()
    graph.add_nodes_from(t.keys())
    for i, j in t.items():
        for k in j:
            graph.add_edge(i, k)

    # gera os grafos dos ramais da rede de baixa tensão
    lv_grids = dict()
    start = nodes_mv
    for h in tqdm(range(2, nodes_mv)):
        prob_ = 0.7
        max_nodes_ = nodes_lv

        t = generate_tree_graph(node=start, tree=dict(), max_nodes=max_nodes_, prob=prob_)
        graph.add_nodes_from(t.keys())
        graph.add_edge(h, start)
        for i, j in t.items():
            for k in j:
                graph.add_edge(i, k)
        start += nodes_lv

    # acréscimo ao dicionário json para indicar nos nós o seu 
    # nome, nível de tensão, cor para representação gráfica 
    # e potências ativas e reativas.
    pf = 0.9 # power factor
    for n in graph:
        graph.node[n]['name'] = n
        if n >= nodes_mv:
            graph.node[n]['color'] = 'rgb(255, 127, 14)'
            graph.node[n]['voltage_level'] = 'low voltage'
            s = (6.0 - 4.0) * random.random() + 4.0
            graph.node[n]['active_power'] = round(s * np.cos(np.arccos(pf)), 3)
            graph.node[n]['reactive_power'] = round(s * np.sin(np.arcsin(pf)), 3)
        else:
            graph.node[n]['voltage_level'] = 'medium voltage'
            graph.node[n]['color'] = 'rgb(31, 119, 180)'
            graph.node[n]['active_power'] = 0.0
            graph.node[n]['reactive_power'] = 0.0
           

    # acréscimo ao dicionário json para indicar nas linhas o seu 
    # nome, comprimento, indicação se linha ou transformador e 
    # presença ou não de chave
    a = 0.2
    b = 0.5
    for i, j in graph.edges.items():
        source, target = i
        graph.edges[i]['name'] = 'Section_%s_%s' % (source, target)
        graph.edges[i]['length'] = round((b - a) * random.random() + a, 3)

        if graph.node[source]['voltage_level'] != graph.node[target]['voltage_level']:
            graph.edges[i]['type'] = 'transformer'
        else:
            graph.edges[i]['type'] = 'line'

        if source == 0 and target == 1:
            graph.edges[i]['switch'] = 'sw_1'
        else:
            graph.edges[i]['switch'] = None

    # write json formatted data
    d = json_graph.node_link_data(graph) # node-link format to serialize
    
    d['transformes'] = []
    transformers_powers = {10.0: 5,
                           15.0: 5,
                           30.0: 15,
                           45.0: 15,
                           75.0: 20,
                           112.5: 15,
                           150.0: 15,
                           225.0: 5,
                           300.0: 5}
    
    powers_list = []
    for i, j in transformers_powers.items():
        for k in range(j):
            powers_list.append(i)
    random.shuffle(powers_list)

    for i, j in graph.edges.items():
        source, target = i
        if graph.node[source]['voltage_level'] != graph.node[target]['voltage_level']:
            tr = {}
            tr['name'] = 'trafo_%s_%s' % (graph.node[source]['name'], graph.node[target]['name'])
            tr['source'] = source
            tr['target'] = target
            tr['power'] = random.choice(powers_list)
            d['transformes'].append(tr)

    # write json
    json.dump(d, open('force.json','w'))
    print('Wrote node-link JSON data to force/force.json')

    return graph

def create_mygrid_model(file):
    data = json.load(file)
    
    vll_mt = p2r(13.8e3, 0.0)
    vll_bt = p2r(380.0, 0.0)
    eg1 = ExternalGrid(name='extern grid 1', vll=vll_mt)

    # switchs
    sw1 = Switch(name='sw_1', state=1)

    # transformers
    t1 = TransformerModel(name="T1",
                          primary_voltage=vll_mt,
                          secondary_voltage=vll_bt,
                          power=225e3,
                          impedance=0.01 + 0.2j)

    phase_conduct = Conductor(id=57)
    neutral_conduct = Conductor(id=44)

    line_model_a = LineModel(loc_a=0.0 + 29.0j,
                             loc_b=2.5 + 29.0j,
                             loc_c=7.0 + 29.0j,
                             loc_n=4.0 + 25.0j,
                             conductor=phase_conduct,
                             neutral_conductor=neutral_conduct,
                             neutral=False)

    phase_conduct_bt = Conductor(id=32)
    line_model_b = LineModel(loc_a=0.0 + 29.0j,
                             loc_b=2.5 + 29.0j,
                             loc_c=7.0 + 29.0j,
                             loc_n=4.0 + 25.0j,
                             conductor=phase_conduct_bt,
                             neutral_conductor=neutral_conduct,
                             neutral=False)

    nodes = dict()
    for node in data['nodes']:
        p = node['active_power'] * 1e3
        q = node['reactive_power'] * 1e3
        s = p + 1j * q
        if node['voltage_level'] == 'medium voltage':
            node_object = LoadNode(name='Node_' + str(node['name']),
                                   power=s,
                                   voltage=vll_mt)

            if node['name'] == 0:
                node_object = LoadNode(name='Node_' + str(node['name']),
                                       power=s,
                                       voltage=vll_mt, external_grid=eg1)                
        elif node['voltage_level'] == 'low voltage':
            node_object = LoadNode(name='Node_' + str(node['name']),
                                   power=s,
                                   voltage=vll_bt)
        nodes[node['name']] = node_object

    sections = dict()
    for link in data['links']:
        if link['type'] == 'line':
            if data['nodes'][link['source']]['voltage_level'] == 'medium voltage':
                if link['switch'] != None:
                    sec_object = Section(name=link['name'],
                                         n1=nodes[link['source']],
                                         n2=nodes[link['target']],
                                         line_model=line_model_a,
                                         switch=sw1,
                                         length=link['length'])
                else:
                    sec_object = Section(name=link['name'],
                                         n1=nodes[link['source']],
                                         n2=nodes[link['target']],
                                         line_model=line_model_a,
                                         length=link['length'])
            if data['nodes'][link['source']]['voltage_level'] == 'low voltage':
                sec_object = Section(name=link['name'],
                                     n1=nodes[link['source']],
                                     n2=nodes[link['target']],
                                     line_model=line_model_b,
                                     length=link['length'])
        elif link['type'] == 'transformer':
            sec_object = Section(name=link['name'],
                                  n1=nodes[link['source']],
                                  n2=nodes[link['target']],
                                  transformer=t1)
        sections[link['name']] = sec_object

    grid_elements = GridElements(name='my_grid_elements')

    grid_elements.add_switch([sw1])
    grid_elements.add_load_node(list(nodes.values()))
    grid_elements.add_section(list(sections.values()))
    grid_elements.create_grid()
    return grid_elements


def main():
    nodes_mv_ = 60
    nodes_lv_ = 5
    graph = generate_grid(nodes_mv=nodes_mv_, nodes_lv=nodes_lv_)
    return graph

if __name__ == '__main__':
    graph = main()
    grid = create_mygrid_model(open('force.json', 'r'))
    calc_power_flow(grid.dist_grids['F0'])
