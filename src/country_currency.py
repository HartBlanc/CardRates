from requests import get
import json

SOMALIA = 706
TURKEY = 792

KOSOVO = 901
N_CYPRUS = 902
SOMALILAND = 903

PROXY = {
    SOMALILAND: SOMALIA,
    N_CYPRUS: TURKEY
}


def limited_recog_state_id(name):
    """
    :param name: A case insensitive string representing the states name.
    :return: An ISO-3166 numeric code in the user-assigned range if
             the match is successful, otherwise None.
    """

    name = name.lower().strip()

    if "kosovo" in name:
        return KOSOVO
    elif ("cyprus" in name) and ("n" in name):
        return N_CYPRUS
    elif "somaliland" in name:
        return SOMALILAND
    else:
        return None


# todo: Split french territories
def get_shapes_topojson_worldatlas(res):
    """
    :param res: Resolution, valid inputs: 10, 50 or 110.
                10m being the most precise resuloution, and largest file size.

    :return: A dictionary of the world atlas in topoJSON format.
             Countries are marked with an int id,
             corresponding to their ISO-3166 numeric code.
             non-UN member states are marked with codes in the 900+ range.

    Note that Natural Earth bundles all the french departments under
    the ISO-3166 code for France (All are EUR).
    """

    parsed = get(f"https://cdn.jsdelivr.net/npm/world-atlas@2/countries-{res}m.json").json()

    for geo in parsed["objects"]["countries"]["geometries"]:
        try:
            geo["id"] = int(geo["id"])
        except KeyError:
            state_id = limited_recog_state_id(geo["properties"]["name"])
            if id:
                geo["id"] = state_id
            else:
                print("topoJSON country missing ISO3166 (Numeric):", geo["properties"]["name"])
                print(geo)
                raise

    return parsed


def get_country_currencies():
    """
    :return: A mapping of ISO-3166 Numeric codes to list of currency data.
             { ISO-3166 numeric : [ {"code": "ISO-4217,
                                     "name": "Currency name",
                                     "symbol": "Currency symbol"},
                                   ...
                                  ],
                                  ...
                }
    """

    country_data = get("https://raw.githubusercontent.com/mledoze/countries/master/dist/countries.json").json()

    result = dict()

    for row in country_data:

        if ('ccn3' not in row) or (not row['ccn3']):
            state_id = limited_recog_state_id(row['name']['common'])
            if state_id:
                row['ccn3'] = state_id
            else:
                print("Curency mapping country missing ISO-3166 (Numeric):", row['name']['common'])
                raise KeyError("ccn3")

        try:
            if not row['currencies']:
                result[int(row['ccn3'])] = []
                continue

            result[int(row['ccn3'])] = [
                {"code": k, 'name': v['name'], 'symbol': v['symbol']}
                for k, v in row['currencies'].items()
            ]
        except KeyError:
            print("Missing Currencies for", row['name']['common'])
            raise

    return result


def main():
    """
    i) Retrieves country -> currencies mapping and world atlas in topoJSON format.
    ii) Merges country -> currencies mapping into the world-atlas. Serialises to topoJSON.
    iii) Creates country -> currency mapping. Serialises to JSON.
    """
    country_currency = get_country_currencies()
    shapes = get_shapes_topojson_worldatlas(110)

    for geo in shapes["objects"]["countries"]["geometries"]:
        try:
            curr_id = country_currency[geo["id"]]
        except KeyError:
            country_currency[geo["id"]] = country_currency[PROXY[geo["id"]]]
            curr_id = country_currency[geo["id"]]

        geo["properties"]["currencies"] = curr_id

    shape_codes = set(geo.get("id") for geo in shapes["objects"]["countries"]["geometries"])
    cc_codes = set(country_currency.keys())

    assert not (shape_codes - cc_codes)

    print("cc_codes - shape_codes:", cc_codes - shape_codes)

    with open("static/country_currency.topo.json", "w") as f:
        json.dump(shapes, f, separators=(',', ':'), ensure_ascii=False)

    with open("static/currency_country_map.json", "w") as f:
        mapping = dict()
        for geo in shapes["objects"]["countries"]["geometries"]:

            country_code = geo.get("id", None)
            currencies = geo["properties"].get("currencies", None)

            if country_code and currencies:
                mapping[country_code] = currencies[0]["code"]

        json.dump(mapping, f, separators=(',', ':'), ensure_ascii=False)


if __name__ == "__main__":
    main()
