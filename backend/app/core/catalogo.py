DESTINOS = [
 {"cidade":"Piripiri","uf":"PI","latitude":-4.2733,"longitude":-41.7769,"atrativos":["Parque Nacional de Sete Cidades","Açude Caldeirão"],"gastronomia":["Maria Isabel","Paçoca de carne"]},
 {"cidade":"Teresina","uf":"PI","latitude":-5.0892,"longitude":-42.8019,"atrativos":["Encontro dos Rios","Ponte Estaiada"],"gastronomia":["Capote","Maria Isabel"]},
 {"cidade":"Parnaíba","uf":"PI","latitude":-2.9059,"longitude":-41.776,"atrativos":["Porto das Barcas","Delta do Parnaíba"],"gastronomia":["Caranguejo","Peixada"]},
 {"cidade":"Fortaleza","uf":"CE","latitude":-3.7319,"longitude":-38.5267,"atrativos":["Praia de Iracema","Dragão do Mar"],"gastronomia":["Baião de dois","Peixada"]},
 {"cidade":"São Luís","uf":"MA","latitude":-2.5297,"longitude":-44.3028,"atrativos":["Centro Histórico","Espigão Costeiro"],"gastronomia":["Arroz de cuxá","Peixe frito"]},
 {"cidade":"Recife","uf":"PE","latitude":-8.0476,"longitude":-34.877,"atrativos":["Marco Zero","Instituto Ricardo Brennand"],"gastronomia":["Bolo de rolo","Tapioca"]},
 {"cidade":"Salvador","uf":"BA","latitude":-12.9777,"longitude":-38.5016,"atrativos":["Pelourinho","Farol da Barra"],"gastronomia":["Acarajé","Moqueca"]},
 {"cidade":"Brasília","uf":"DF","latitude":-15.7939,"longitude":-47.8828,"atrativos":["Catedral Metropolitana","Praça dos Três Poderes"],"gastronomia":["Arroz com pequi","Pamonha"]},
]

def catalogo(cidade, uf):
    import unicodedata
    def norm(s): return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
    return next((d for d in DESTINOS if norm(d['cidade'])==norm(cidade) and d['uf']==uf), {})
