from fuzzywuzzy import process
from scipy.optimize import linear_sum_assignment
from numpy import array
import operator
import re

dateChoices = ["Date", "Date Opération", "Oper", "Dates", "Dates Oper"]
designationChoices = ["Désignation", "Nature de l'opération", "Operation-reference", "Reference", "Libellé", "Libelle"]
debitChoices = ["Débit"]
creditChoices = ["Crédit"]


class Tinder:
    @staticmethod
    def computeDistancesToLabels(text, choices, limit=5):
        """
        Return list of tuples: [(choiceItem, score),...]
        """
        return process.extract(text, choices, limit=limit)
    
    @staticmethod
    def computeComplementaryScoresToLabels(text, choices, limit=5):
        """
        Return list of tuples: [(choiceItem, score),...]
        """
        arr = process.extract(text, choices, limit=limit)
        return list(map(lambda x: 100 - x[1], arr))

    @staticmethod
    def bestTextMatch(text, choices):
        """
        Return int: score of the best match
        """
        return process.extract(text, choices, limit=1)[0][1]

    @staticmethod
    def buildDistancesMatrix(refKeywords, incomingKeywords):
        listOfScores = [Tinder.computeComplementaryScoresToLabels(bankItem, incomingKeywords) for bankItem in refKeywords]
        return array(listOfScores)

    @staticmethod
    def matchMunkresFromMatrix(matrix):
        rowInd, colInd = linear_sum_assignment(matrix)
        return {"rowIndices": rowInd, "colIndices": colInd}

    @staticmethod
    def computeBorneInf(distanceObject):
        borneInf = max(distanceObject.items(), key=operator.itemgetter(1))
        return {"label": borneInf[0], "distance": borneInf[1]}

class BankStatement:
    @staticmethod
    def getHeaders(table):
        if not len(table.rows):
            return None
        return list(map(lambda x: x.text, table.rows[0].cells))
    
    @staticmethod
    def getCounterpartyStatement(statementItem):
        result = None
        if (statementItem['Credit'] is None and statementItem['Debit'] is None):
            raise Exception('No debit or Credit identified in statement')
        else:
            result = statementItem.copy()
            result['Credit'] = statementItem['Debit']
            result['Debit'] = statementItem['Credit']
            result['Compte'] = '51410000'
        return result

    @staticmethod
    def fetchClosestItems(text):
        result = {
            "Date": Tinder.bestTextMatch(text, dateChoices),
            "Designation": Tinder.bestTextMatch(text, designationChoices),
            "Debit": Tinder.bestTextMatch(text, debitChoices),
            "Credit": Tinder.bestTextMatch(text, creditChoices)
        }
        return result

    @staticmethod
    def hasValidHeaders(headers, treshold=30):
        result = True
        counter = 0
        for item in headers.keys():
            if headers[item]['score'] < treshold:
                counter += 1
                if counter == 2:
                    result = False
                    break
        return result

    @staticmethod
    def isValidStatement(statement):
        result = True
        if (statement['Debit'] == None or statement['Debit'] == "") and (statement['Credit'] == None or statement['Credit'] == ""):
            result = False
        if (not BankStatement.hasValidPrice(statement['Debit'])) and (not BankStatement.hasValidPrice(statement['Credit'])):
            return False
        if statement['Date'] == '' or statement['Date'] is None:
            return False
        return result

    @staticmethod
    def parsePrice(priceString):
        match = None
        if type(priceString) is str:
            match = re.match(r"^([\d. ]+)([.,]\d{1,2})*", priceString)
        return match[0] if match else None
    
    @staticmethod
    def hasValidPrice(priceString):
        match = None
        if type(priceString) is str:
            match = re.match(r"^\d+([.,]\d{1,2})*", priceString)
        return match is not None and len(match[0]) + 3 >= len(priceString.strip())

    @staticmethod
    def parseEntry(entry, header):
        if (header=='Debit' or header == 'Credit') and type(entry) is str:
            return BankStatement.parsePrice(entry)
        else:
            return entry

    @staticmethod
    def findHeadersIndices(itemsList, minTreshold=60):
        result = {
        "Date": {"index": None, "score": 0, "matchedText": None},
        "Designation": {"index": None, "score": 0, "matchedText": None},
        "Debit": {"index": None, "score": 0, "matchedText": None},
        "Credit": {"index": None, "score": 0, "matchedText": None}
        }
        for idx, item in enumerate(itemsList):
            borneInf = Tinder.computeBorneInf(BankStatement.fetchClosestItems(item))
            if borneInf["distance"] >= minTreshold and borneInf["distance"] > result[borneInf["label"]]["score"] :
                result[borneInf["label"]]["index"] = idx
                result[borneInf["label"]]["score"] = borneInf["distance"]
                result[borneInf["label"]]["matchedText"] = item
        return result