import numpy as np
from profiel import profieldictionary

# returns the table from the list of tables by tablename if it doesnt exist an exception is raised
def Findtable(tablename, tables):
    for table in tables:
        if table[0] == tablename:
            return table
    raise Exception(f"Could find the table {tablename}")

# This function fills in all the rod properties for the so when the user asks for the unity checks from the dictionary there are correctly calculated
def fill_in_rod_properties(rod, tables):
    property_dict = {}
    property_dict, (aantal, profiel) = propertiesMaterialen(property_dict, rod, tables)
    property_dict = propertiesProfiel(property_dict, profiel, aantal)
    property_dict = propertiesBelastingen(property_dict)
    property_dict = propertiesClassificatie(property_dict)
    property_dict = toetsingDoorsnede(property_dict)
    return property_dict

def propertiesMaterialen(property_dict, rod, tables):
    STAVEN = Findtable("STAVEN", tables)
    Nr, Profiel = STAVEN[2][rod-1][3].split(":")
    PROFIEL = Findtable("PROFIELEN [mm]", tables)
    property_dict["S"] = int(PROFIEL[2][int(Nr)-1][2].split(":")[1][1:])
    property_dict["fy"] = property_dict["S"]
    match property_dict["fy"]:
        case 235:
            property_dict["fu"] = 360
        case 275:
            property_dict["fu"] = 430
        case 355:
            property_dict["fu"] = 510
        case 440:
            property_dict["fu"] = 550
    property_dict["E"] = 210000
    property_dict["epsilon"] = 235/property_dict["fy"]
    property_dict["lambda"] = float(np.pi*np.sqrt(property_dict["E"]/property_dict["fy"]))
    return property_dict, Profiel.split("*")

def propertiesProfiel(property_dict, profiel, aantal):
    property_dict["Type Gording"] = profiel
    property_dict["aantal"] = int(aantal)
    profielpropertie = profieldictionary[profiel]
    property_dict["h"] = profielpropertie[0]
    property_dict["b"] = profielpropertie[1]
    property_dict["tw"] = profielpropertie[2]
    property_dict["tf"] = profielpropertie[3]
    property_dict["wel"] = profielpropertie[4]
    property_dict["wpl"] = profielpropertie[5]
    property_dict["A"] = profielpropertie[8]
    property_dict["r"] = profielpropertie[9]
    property_dict["ly"] = profielpropertie[10]
    property_dict["G"] = profielpropertie[12]
    property_dict["Hw"] = property_dict["b"]-2*property_dict["tf"]
    property_dict["Av"] = property_dict["A"]-(2*property_dict["b"]*property_dict["tf"])+((property_dict["tw"]+2*property_dict["r"])*property_dict["tf"])
    property_dict["Af"] = property_dict["b"] * property_dict["tf"]
    property_dict["Aw"] = property_dict["tw"] * property_dict["Hw"]
    property_dict["h/b"] = property_dict["h"] / property_dict["b"]
    return property_dict

def propertiesBelastingen(property_dict):
    property_dict["UGT Normaalkracht"] = 0
    property_dict["UGT Dwarskracht"] = 0
    property_dict["UGT Moment"] = 0

    return property_dict

def safe_imperfectie(property_dict):
        try:
            rek_bm = property_dict["Rek. buigend moment"]()
            rek_w_bm = property_dict["Rek. weerstand tegen buigend moment"]()
            rek_nk = property_dict["Rek. normaalkracht"]()
            rek_w_tt = property_dict["Rek. weerstand tegen trek"]()
            fy = property_dict["fy"]

            # Check for zero denominators
            if rek_w_bm == 0 or rek_w_tt == 0:
                return 0

            first_term = (rek_bm / rek_w_bm) * fy
            denominator = 2 * (rek_bm / rek_w_bm) * fy

            # Prevent division by zero in second term
            if denominator == 0:
                return 0

            second_term = (rek_nk / rek_w_tt) * fy / denominator

            return first_term + second_term

        except ZeroDivisionError:
            return 0
        except KeyError as e:
            print(f"Missing key: {e}")
            return 0


def propertiesClassificatie(property_dict):
    property_dict["lijf"] = (property_dict["h"]-2*property_dict["tf"]-2*property_dict["r"])/property_dict["tw"]/property_dict["epsilon"]
    property_dict["flens"] = (property_dict["b"]/2 -(property_dict["tw"]/2)-property_dict["r"])/property_dict["tf"]/property_dict["epsilon"]
    if property_dict["h/b"] > 1.2 and property_dict["tf"] <= 40:
        property_dict["knikkromme y-y"] = "a"
        property_dict["knikkromme z-z"] = "b"
    elif property_dict["h/b"] > 1.2 and property_dict["tf"] > 40 and property_dict["tf"] <= 100:
        property_dict["knikkromme y-y"] = "b"
        property_dict["knikkromme z-z"] = "c"
    elif property_dict["h/b"] <= 1.2 and property_dict["tf"] <= 100:
        property_dict["knikkromme y-y"] = "b"
        property_dict["knikkromme z-z"] = "c"
    elif property_dict["h/b"] <= 1.2 and property_dict["tf"] > 100:
        property_dict["knikkromme y-y"] = "d"
        property_dict["knikkromme z-z"] = "d"
    else:
        raise Exception("either h/b is not correct or tf is not correctly check them again")

    if property_dict["lijf"] < 72:
        property_dict["doorsnede klasse buiging"] = 1
    elif property_dict["lijf"] < 83:
        property_dict["doorsnede klasse buiging"] = 2
    elif property_dict["lijf"] < 124:
        property_dict["doorsnede klasse buiging"] = 3
    else:
        property_dict["doorsnede klasse buiging"] = 4

    if property_dict["lijf"] < 33:
        property_dict["doorsnede klasse druk"] = 1
    elif 33 < property_dict["lijf"] < 38:
        property_dict["doorsnede klasse druk"] = 2
    elif 38 < property_dict["lijf"] < 42:
        property_dict["doorsnede klasse druk"] = 3
    elif property_dict["lijf"] > 42:
        property_dict["doorsnede klasse druk"] = 4

    property_dict["imperfectie"] = safe_imperfectie(property_dict)

    property_dict["temp1"] = lambda: (
    property_dict["lijf"] * ((13 * property_dict["imperfectie"]) - 1)
    if property_dict["imperfectie"] > 0.5
    else property_dict["lijf"] * property_dict["imperfectie"]
    )

    property_dict["temp2"] = lambda: (
        396 if property_dict["imperfectie"] > 0.5 else 36
    )

    property_dict["temp3"] = lambda: (
        456 if property_dict["imperfectie"] > 0.5 else 41.5
    )

    property_dict["doorsnede klasse druk en buiging"] = lambda: (
        1 if property_dict["temp1"]() < property_dict["temp2"]() and property_dict["temp1"]() < property_dict["temp3"]()
        else 2 if (property_dict["temp1"]() > 51 and property_dict["temp1"]() < property_dict["temp3"]()) or 
                (property_dict["temp1"]() < 51 and property_dict["temp1"]() > property_dict["temp3"]())
        else 3 if property_dict["temp1"]() > property_dict["temp2"]() and property_dict["temp1"]() > property_dict["temp3"]() else -1)
    return property_dict

############################################################################################################################################################
# Below here are the calculations for the unity checks
############################################################################################################################################################

def toetsingDoorsnede(property_dict):
    property_dict = toetsingNormaalkracht(property_dict)
    property_dict = toetsingBuigendMoment(property_dict)
    property_dict = toetsingDwarskracht(property_dict)
    property_dict = toetsingBuigingEnDwarskracht(property_dict)
    property_dict = toetsingBuigingEnNormaalkracht(property_dict)
    property_dict = toetsingBuigingEnDwarskrachtEnNormaalkracht(property_dict)
    return property_dict

def toetsingNormaalkracht(property_dict):
    property_dict["Rek. normaalkracht"] = lambda: property_dict["UGT Normaalkracht"]*1.1/property_dict["aantal"]
    property_dict["Rek. weerstand tegen trek"] = lambda: (property_dict["fy"]*property_dict["A"])/1/1000
    property_dict["u.c normaalkracht"] = lambda: property_dict["Rek. normaalkracht"]()/ property_dict["Rek. weerstand tegen trek"]()
    return property_dict

def compute_u_c_buigend_moment(property_dict):
    property_dict["Rek. buigend moment"] = lambda: property_dict["UGT Moment"]*1.1/property_dict["aantal"]
    if property_dict["doorsnede klasse buiging"] <= 2:
        property_dict["Wy-y"] = property_dict["wpl"]
        property_dict["Rek. weerstand tegen buigend moment"] = lambda: (property_dict["fy"]*property_dict["wpl"])/1/1000000
    else:
        property_dict["Wy-y"] = property_dict["wel"]
        property_dict["Rek. weerstand tegen buigend moment"] = lambda: (property_dict["fy"]*property_dict["wel"])/1/1000000
    return property_dict["Rek. buigend moment"]()/ property_dict["Rek. weerstand tegen buigend moment"]()

def toetsingBuigendMoment(property_dict):
    property_dict["u.c buigend moment"] = lambda: compute_u_c_buigend_moment(property_dict)
    return property_dict

def compute_u_c_dwarskracht(property_dict):
    property_dict["Rek. dwarskracht"] = lambda: property_dict["UGT Dwarskracht"]*1.1/property_dict["aantal"]
    if property_dict["doorsnede klasse druk"] <= 2:
        property_dict["Rek. dwarskracht vloeien"] = property_dict["Av"]*property_dict["S"]/np.sqrt(3)/1/1000
    else:
        property_dict["Rek. dwarskracht vloeien"] = property_dict["Aw"]*property_dict["S"]/np.sqrt(3)/1/1000
    return property_dict["Rek. dwarskracht"]()/ property_dict["Rek. dwarskracht vloeien"]

def toetsingDwarskracht(property_dict):
    property_dict["u.c dwarskracht"] = lambda: compute_u_c_dwarskracht(property_dict)
    return property_dict

def compute_u_c_buiging_en_dwarskracht(property_dict):
    if property_dict["u.c dwarskracht"]() <= 0.5:
        property_dict["rho"] = lambda: 0
    else:
        property_dict["rho"] = lambda: property_dict["UGT Dwarskracht"]*1.1/property_dict["aantal"]
    property_dict["My,V,Rd"] = lambda: ((property_dict["Wy-y"]-((property_dict["rho"]() * (property_dict["Aw"]**2))/(4*property_dict["tw"])))*property_dict["fy"]/1)/1000000
    if property_dict["Rek. buigend moment"]() == 0:
        return 0
    else:
        return property_dict["My,V,Rd"]() / property_dict["Rek. buigend moment"]()

def toetsingBuigingEnDwarskracht(property_dict):
    property_dict["u.c buiging en normaalkracht"] = lambda: compute_u_c_buiging_en_dwarskracht(property_dict)
    return property_dict

def compute_u_c_buiging_en_normaalkracht(property_dict):
    if property_dict["doorsnede klasse druk en buiging"]() < 3:
        property_dict["NEd/hw*tw*fy/2*gm0"] = lambda: (property_dict["Rek. normaalkracht"]()*1000)/(property_dict["Hw"]*property_dict["tw"]*property_dict["fy"])/2
        property_dict["a"] = (property_dict["A"]-(2*property_dict["b"]*property_dict["tf"]))/property_dict["A"]
        if property_dict["u.c normaalkracht"]() <= 0.25 and property_dict["NEd/hw*tw*fy/2*gm0"]() <= 1:
            property_dict["My,V,Rd"] = lambda: property_dict["Rek. weerstand tegen buigend moment"]()
        else:
            property_dict["My,V,Rd"] = lambda: property_dict["Wy-y"]*property_dict["fy"]*((1-property_dict["u.c normaalkracht"]())/(1-(0.5*property_dict["a"])))/1000000
        return property_dict["Rek. buigend moment"]() / property_dict["My,V,Rd"]()
    else:
        return (property_dict["Rek. normaalkracht"]()*1000)/(property_dict["A"]*property_dict["fy"])+(property_dict["Rek. buigend moment"]()*1000000/(property_dict["wel"]*property_dict["fy"]))


def toetsingBuigingEnNormaalkracht(property_dict):
    property_dict["u.c buiging en normaalkracht"] = lambda: compute_u_c_buiging_en_normaalkracht(property_dict)
    return property_dict

def compute_u_c_buiging_en_dwarskracht_en_normaalkracht(property_dict):
    if property_dict["doorsnede klasse druk en buiging"]() < 3:
        if property_dict["u.c dwarskracht"]() <= 0.5:
            rho2 = 0
        else:
            rho2 = ((((2 * property_dict["UGT Dwarskracht"]) / property_dict["aantal"]) / property_dict["Rek. dwarskracht vloeien"]) - 1) ** 2

        NVz_Rd = ((property_dict["A"] * property_dict["fy"]) - (rho2 * property_dict["Av"] * property_dict["fy"])) / 1000

        a1_val = ((property_dict["A"] - (2 * property_dict["b"] * property_dict["tf"])) / property_dict["A"])
        if a1_val < 0.5:
            a1 = a1_val
        else:
            a1 = 0.5

        a2 = a1 * (1 - rho2)

        MN_y_Rd = ((property_dict["Wy-y"] - ((rho2 * property_dict["Av"] ** 2) / (4 * property_dict["tw"]))) * property_dict["fy"]) / 1e6

        val = (
            (property_dict["Rek. buigend moment"]() / MN_y_Rd) +
            ((property_dict["Rek. normaalkracht"]() / NVz_Rd) - (a2 / 2)) / (1 - (a2 / 2))
        )
        return val

    else:
        # Put your else calculation here, if any. For now, just 0 or None:
         # property_dict["My,Ed/My,N,f,Rd"] = (property_dict["Rek. buigend moment"]*10^6/(((E23*E22^3)-(E23*E32^3))/(6*E22)*property_dict["fy"])))
            # if (E32/E24)>(72*E15/1):
            #     if E98<=0,25 and E100<=1:
            #         property_dict["My,Ed/My,N,Rd"] = property_dict["Rek. weerstand tegen buigend moment"]
            #     else:
            #         property_dict["My,Ed/My,N,Rd"] = E73*property_dict["fy"]*((1-E98)/(1-(0,5*E102)))/10^6
        return 0

def toetsingBuigingEnDwarskrachtEnNormaalkracht(property_dict):
    property_dict["u.c buiging en dwarskracht en normaalkracht"] = lambda: compute_u_c_buiging_en_dwarskracht_en_normaalkracht(property_dict)
    return property_dict