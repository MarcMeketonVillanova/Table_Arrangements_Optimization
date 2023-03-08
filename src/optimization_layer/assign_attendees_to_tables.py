import networkx as nx

from src.entity.attendee import Attendee
from src.entity.table import Table


def assign_attendees_to_tables(attendees_to_be_assigned, tables_to_be_assigned) -> list[tuple[Attendee, Table]]:
    g = nx.DiGraph()

    # items_to_be_assigned = [item for item in items if attendees[item].assigned_to_group == -1]
    m = len(attendees_to_be_assigned)
    n = len(tables_to_be_assigned)

    for attendee in attendees_to_be_assigned:
        g.add_node(attendee.item_id, attendee=attendee, demand=-1)
    for table in tables_to_be_assigned:
        g.add_node(f'table_{table.table_id}', table=table, demand=1)
    g.add_node('Fake', demand=m - n)

    for attendee in attendees_to_be_assigned:
        for table in tables_to_be_assigned:
            score = table.score_if_attendee_is_added_to_table(attendee)
            g.add_edge(attendee.item_id, f'table_{table.table_id}', weight=score)

    if m < n:
        for table in tables_to_be_assigned:
            g.add_edge('Fake', f'table_{table.table_id}', weight=0.0)
    else:
        for attendee in attendees_to_be_assigned:
            g.add_edge(attendee.item_id, 'Fake', weight=0.0)
    # with open(r'c:/temp/edges.txt','w') as ff:
    #     ff.write(str(g.edges.data()))

    flows = nx.min_cost_flow(g, demand='demand', weight='weight')

    attendee_assigned_to_table: list[tuple[Attendee, Table]] = list()
    for from_node, to_nodes in flows.items():
        if 'attendee' in g.nodes[from_node]:
            attendee = g.nodes[from_node]['attendee']

            # should be exactly one to_node with positive value
            to_node = [_to_node for _to_node, value in to_nodes.items() if value > 0.01][0]

            if 'table' in g.nodes[to_node]:
                table = g.nodes[to_node]['table']
                attendee_assigned_to_table.append((attendee, table))

    return attendee_assigned_to_table
