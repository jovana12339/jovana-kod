import cv2
import serial
import time

# =========================
# ARDUINO
# =========================
### Ubaciti proveru da li je Arduino povezan
arduino = serial.Serial("COM4", 9600, timeout=1)
time.sleep(2)

# =========================
# KAMERA
# =========================
### Ubaciti proveru da li je kamera povezana
kamera = cv2.VideoCapture(1)

# Početni uglovi
ugao_levo_desno = 90
ugao_gore_dole = 90

### Poslati početne uglove na Arduino

# =========================
# PODESAVANJE BRZINE
# =========================

# Koliko stepeni se pomera svaki put
KORAK = 1

# Veća vrednost = sporije pomeranje
RAZMAK = 0.18

# Koliko krug sme da bude udaljen od centra
# a da kamera još uvek stoji
MRTVA_ZONA = 45

poslednje_pomeranje = 0


while True:

    ret, slika = kamera.read()

    if not ret:
        print("Kamera ne radi!")
        break

    visina, sirina = slika.shape[:2]

    # Centar slike
    centar_x = sirina // 2
    centar_y = visina // 2

    # =========================
    # CRVENA BOJA
    # =========================

    hsv = cv2.cvtColor(slika, cv2.COLOR_BGR2HSV)

    maska1 = cv2.inRange(
        hsv,
        (0, 120, 70),
        (10, 255, 255)
    )

    maska2 = cv2.inRange(
        hsv,
        (170, 120, 70),
        (180, 255, 255)
    )

    maska = maska1 | maska2

    # =========================
    # TRAŽENJE CRVENOG KRUGA
    # =========================

    konture, _ = cv2.findContours(
        maska,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if konture:
        ### Ovde izvlačite samo najveću konturu, 
        # bolje je da prođete kroz sve konture i 
        # da nađete onu koja je najveća i približno kružna, 
        # računate cirkularity kao 
        # 4 * pi * area / (perimeter^2) i uzimate onu koja je najbliža 1.0, 
        # jer konture mogu biti nepravilne i ne moraju biti krugovi.
        # OpenCV ima funkciju contourArea koja računa površinu konture, 
        # a za obim možete koristiti arcLength.
        # Time ćete dobiti preciznije rezultate i izbeći greške u praćenju.


        kontura = max(
            konture,
            key=cv2.contourArea
        )

        if cv2.contourArea(kontura) > 500:

            M = cv2.moments(kontura)

            if M["m00"] != 0:

                # CENTAR CRVENOG KRUGA
                x = int(M["m10"] / M["m00"])
                y = int(M["m01"] / M["m00"])

                # =========================
                # PRIKAZ
                # =========================

                cv2.circle(
                    slika,
                    (x, y),
                    10,
                    (255, 0, 0),
                    -1
                )

                cv2.circle(
                    slika,
                    (centar_x, centar_y),
                    10,
                    (0, 255, 255),
                    -1
                )

                cv2.line(
                    slika,
                    (centar_x, centar_y),
                    (x, y),
                    (0, 255, 0),
                    2
                )

                # =========================
                # GREŠKA
                # =========================

                greska_x = x - centar_x
                greska_y = y - centar_y

                sada = time.time()

                # =========================
                # SPORO POMERANJE
                # =========================

                if sada - poslednje_pomeranje >= RAZMAK:

                    # ---------------------------------
                    # LEVO / DESNO
                    # ---------------------------------

                    # KRUG LEVO -> KAMERA DESNO
                    if greska_x < -MRTVA_ZONA:

                        ugao_levo_desno += KORAK

                    # KRUG DESNO -> KAMERA LEVO
                    elif greska_x > MRTVA_ZONA:

                        ugao_levo_desno -= KORAK

                    # ---------------------------------
                    # GORE / DOLE
                    # ---------------------------------

                    # KRUG GORE -> KAMERA DOLE
                    if greska_y < -MRTVA_ZONA:

                        ugao_gore_dole += KORAK

                    # KRUG DOLE -> KAMERA GORE
                    elif greska_y > MRTVA_ZONA:

                        ugao_gore_dole -= KORAK

                    # Ograničenje 0-180
                    ugao_levo_desno = max(
                        0,
                        min(180, ugao_levo_desno)
                    )

                    ugao_gore_dole = max(
                        0,
                        min(180, ugao_gore_dole)
                    )
                    ### Ovde stavite ispitivanje uglovla pre slanja da bi mogli 
                    # da vidite ako šaljete neke loše vrednosti na Arduino
                    # Vi sad ispisujete te vrednosti i kad ih ne šaljete.
                    # Pošalji oba serva
                    arduino.write(
                        f"{ugao_levo_desno} {ugao_gore_dole}\n".encode()
                    )

                    poslednje_pomeranje = sada

                print(
                    f"Krug: X={x}, Y={y} | "
                    f"Servo D9={ugao_levo_desno} | "
                    f"Servo D10={ugao_gore_dole}"
                )

    # =========================
    # PRIKAZ KAMERE
    # =========================

    cv2.imshow(
        "PRAĆENJE CRVENOG KRUGA",
        slika
    )

    # ESC za izlaz
    if cv2.waitKey(1) & 0xFF == 27:
        break


kamera.release()
arduino.close()
cv2.destroyAllWindows()
