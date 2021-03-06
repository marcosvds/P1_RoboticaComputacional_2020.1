# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 18:47:06 2020

@author: Enrico Damiani, Marcos Vinícius
"""

#importando bibliotecas
import cv2
import numpy as np
import math
from cv_bridge import CvBridge
br = CvBridge()

def auto_canny(image, sigma=0.33):
    
    v = np.median(image)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)
    
    return edged


#Calcula a reta para 2 pontos
def LineCalculator (P1, P2):
    
    coefAng = float(P2[1] - P1[1]) / float(P2[0] - P1[0])
    coefLin = (P1[1] - (coefAng * P1[0]))

    return [coefAng, coefLin] 

#Escolhe as retas
def ChooseLine (angCoefGen):

    maxIndex = angCoefGen.index(max(angCoefGen))
    minIndex = angCoefGen.index(min(angCoefGen))
    
    return maxIndex, minIndex

#Entra o ponto de encontro para 2 retas
def IntPoin (coefAngGen, coefLinGen, indMax, indMin):
    
    coefAngMax = coefAngGen[indMax]
    coefLinMax = coefLinGen[indMax]

    coefAngMin = coefAngGen[indMin]
    coefLinMin = coefLinGen[indMin]

    xs = float(coefLinMax) - float(coefLinMin)
    xi = float(coefAngMin) - float(coefAngMax)

    if xi != 0:
        x = int(xs/xi)
    else:
        x = int(xs/0.1)

    y =  int((coefAngMax * x) + coefLinMax)   

    return x, y

def CheckAngCoef (coefAngGen, indMax, indMin):

    coefAngMax = coefAngGen[indMax]
    coefAngMin = coefAngGen[indMin]

    if coefAngMax < 0 and coefAngMin < 0:
        return "Negative"
    
    elif coefAngMax > 0 and coefAngMin > 0:
        return "Positive"

    else:
        return "Different"


def CheckAngCoefValue (coefAngGen, indMax, indMin):

    coefAngMax = coefAngGen[indMax]
    coefAngMin = coefAngGen[indMin]

    if abs (coefAngMax) < 0.2 and coefAngMin <0:
        return "Max0"
    
    elif abs(coefAngMin) < 0.2  and coefAngMax > 0:
        return "Min0"

    else:
        return "None"

def CheckPoint(x2Max, x1Min, withFrame):

    if x2Max < (withFrame/2) and x1Min < (withFrame/2):
        
        return "LA"
        
    
    elif x2Max > (withFrame/2) and x1Min > (withFrame/2):

        return "RA"


    else:

        return 'None'


def Draw (frame, pex, pey, p1x, p1y, p2x, p2y):

    cv2.circle(frame,(pex, pey),15,(0,255,0),3) #Plotando circulo
    cv2.circle(frame,(pex, pey),5,(0,0,255),3)
    
    cv2.line(frame, (p1x, p1y), (pex, pey), (0, 255, 0), 3, cv2.LINE_AA) #Plotando reta
    cv2.line(frame, (p2x, p2y), (pex, pey), (0, 255, 0), 3, cv2.LINE_AA)

    return None 

    

#Delimitaçõa do amarelo, interfere na máscara
hsv1_a = np.array([23,65,65], dtype=np.uint8)
hsv2_a = np.array([30, 255, 255], dtype=np.uint8)

def main(frame):

    #Máscara
    frame = br.compressed_imgmsg_to_cv2(frame) #Descomprimindo a imagem
    with_frame = frame.shape[0] #Largura do frame em px
    Height_frame = frame.shape[1] #Altura do frame em px
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #Transformando em RGB de BGR
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY) #Transformando RGB em Gray
    img_hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV) #Transformando RGB em HSV
    maskb = cv2.inRange(img_gray, 210, 255) #Mascara Branco
    maska = cv2.inRange(img_hsv, hsv1_a, hsv2_a) #Mascara Amarelo
    maskp = maskb & maska #Soma das mascaras
    maskf = maskb - maskp #Retorna o que e branco - Branco final
    not_mask = cv2.bitwise_not(maskf) #Tudo que nao e branco
    res = cv2.bitwise_and(img_gray,img_gray, mask = not_mask) #todo pixel que nao e branco fica em cinza
    res2 = cv2.cvtColor(res, cv2.COLOR_GRAY2RGB) #Transformando img gray para ter RGB
    res3 = cv2.bitwise_and(frame,frame, mask= maskf) #todo pixel que obtido em maskf fica na cor original - branco
    final = cv2.bitwise_or(res3, res2) #Junta res3 com res2

    blur = cv2.GaussianBlur(maskf,(5,5),0) #Define melhor a imagem
    bordas = auto_canny(blur) #Pega os contorno da imagem


    #Encontra as linhas na imagem
    linesList = cv2.HoughLinesP(bordas ,rho = 4,theta = 1*np.pi/90,threshold = 80,minLineLength = 100,maxLineGap = 50) #lista de lista com posicao inicial e final

    x1 = []
    y1 = []
    x2 = []
    y2 = []
    angCoef = []
    linCoef = []


    #Encontra as retas, substituindo na função, e adiciona os coeficientes dessa em listas
    if linesList is not None: 
        for i in range(0, len(linesList)):
            l = linesList[i][0]
            line = LineCalculator((l[0], l[1]), (l[2], l[3]))

            x1.append(l[0])
            y1.append(l[1])
            x2.append(l[2])
            y2.append(l[3])
            angCoef.append(line[0])
            linCoef.append(line[1])
            
        iMax, iMin = ChooseLine(angCoef)
        
        pointX, pointY = IntPoin(angCoef, linCoef, iMax, iMin) #Calcula o ponto de fuga por meio da reta de maior e menor coeficiente angular
        
        turnParameter = CheckAngCoef(angCoef, iMax, iMin) #Compara os coeficientes angular, se forem maior, menor ou diferente - a partir disso consegue determinar se esta na borda, esquerda, direita ou nao.

        checker0 = CheckAngCoefValue(angCoef, iMax, iMin)

        pointParameter = CheckPoint(x2[iMax], x1[iMin], with_frame) #indice seleciona o coeficiente angular
        
        Draw(final, pointX, pointY, x2[iMax], y2[iMax], x1[iMin], y1[iMin])

    else:

        pointX = 0
        pointY = 0
        turnParameter = "Different"
        pointParameter = "None"
        checker0 = "None"
    
    return final, (pointX, pointY), turnParameter, pointParameter, checker0
