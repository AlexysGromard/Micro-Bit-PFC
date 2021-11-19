
from microbit import *
import music
import radio


rps_images = {
    0: Image("00900:"
             "09990:"
             "99599:"
             "09990:"
             "00900"
             ),
    1: Image("99900:"
             "90090:"
             "90009:"
             "90009:"
             "99999"
             ),
    2: Image("99009:"
             "99090:"
             "00900:"
             "99090:"
             "99009"
             ),
    "restart": Image(
             "09990:"
             "00009:"
             "99909:"
             "99009:"
             "90990"
             ),
}


def connect_to(nb):
    """Se connecter à l'autre joueur"""
    radio.config(group=nb) 
    radio.on()  # Démarre la communication
    radio.send("OK")  # Prévient que c'est Ok
    # Attends l'autre joueur
    waiting_status(50, radio.receive, lambda msg: msg is None and msg != "OK")
    radio.send("OK")  # Renvoie un message


def select(c, show_func, *, allow_hold=False, hold_speed=200, on_change_func=None):
    """Choisi un élément parmis une liste
        Renvoie l'index choisi."""
    li = 0  # Index choisi
    max_index = len(c) - 1  # Taille de la liste
    
    pressed, added, times = [True, True], [0, 0], [-1, -1]
    time_diff = lambda t1, t2: abs(t1 - t2)
    
    def testfor(index, nb, l):
        """Test si un bouton est appuyé"""
        valid_press = time_diff(times[0], times[1]) > 20 and running_time() - times[index] > 20
        if pressed[index] and valid_press:
            # Si le bouton est appuyé mais que l'autre ne l'est pas
            diff = running_time() - times[index]
            if diff // hold_speed >= added[index]:
                # Si le bouton est resté enfoncé on continue d'ajouté
                if allow_hold or added[index] == 0:
                    nb = l(nb)  # On ajoute ou diminue (l est une lambda)
                    if on_change_func is not None:
                        on_change_func()
                added[index] += 1
        return nb  # On revoie le nouveau nombre
    
    while any(pressed):  # On attends que tous les boutons soit lâchés
        pressed = [button_a.is_pressed(), button_b.is_pressed()]
 
    is_valid = False
    while not is_valid:  # Temps que non choisis
        pressed = [button_a.is_pressed(), button_b.is_pressed()]
        for i in range(2):
            if pressed[i] and times[i] < 0:
                # Si les boutons sont pressés on garde la "date" actuelle
                times[i] = running_time()
            elif not pressed[i]:
                # Sinon on indique qu'il n'est pas pressé
                times[i] = -1
                added[i] = 0
                
        if all(pressed):  # Si tous les boutons sont appuyés
            if time_diff(times[0], times[1]) <= 20:  # Et qu'ils ont été pressés en même temps
                is_valid = True  # On choisit ce temps
            added = [1000000, 1000000]
        else:  # Sinon on incrémente / diminue le timer
            li = testfor(0, li, lambda x: x - 1)
            li = testfor(1, li, lambda x: x + 1)
        
        if li > max_index: li = 0  # On garde la valeur
        if li < 0: li = max_index  # entre 0 et 9
        
        display.show(show_func(li))  # On montre
    
    return li
        

def select_canal():
    """Permet de sélectionner un joueur
    Les deux joueurs prennent le même"""
    lst = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    return select(lst, lambda i: lst[i],
                  allow_hold=True)


def choice():
    """Fonction pour choisir
    pierre feuille ou ciseaux"""
    playsound = lambda: music.pitch(988,1)
    choice_rps = select(
                    [0, 1, 2],
                    lambda i: rps_images[i],
                    on_change_func=playsound,
                    allow_hold=True,
                    hold_speed=300
                 )
    
    display.show(Image.YES)
    music.play(music.BA_DING)
    sleep(400)
    return choice_rps
    
    while True:
        if button_b.is_pressed() and button_a.is_pressed(): 
            
            break
        if button_b.is_pressed() and choice_rps < 2:
            choice_rps += 1
            music.pitch(988,1)
        elif button_a.is_pressed() and choice_rps > 0:
            choice_rps -= 1
            
        display.show(rps_images[choice_rps])
        sleep(150)
    return choice_rps



def wait_ec():
    """Renvoie le choix de
    l'ennemi s'il y en a un"""
    r = radio.receive()
    temp = -1
    if r is not None:
        r = r.split(":")
        if r[0] == "CHOICE":
            temp = int(r[1])
    return temp


def waiting_status(clock_speed, function, condition):
    """Affiche une aiguille qui tourne à la vitesse
    clock_speed. Elle fait appelle à la fonction donnée
    en paramètres afin de vérifier la condition. Lorsque
    la condition est validé la fonction se stop"""
    
    c = 0
    last_clock = running_time()
    temp = function()
    while condition(temp):
        temp = function()
        if running_time() + clock_speed > last_clock:
            last_clock += clock_speed
            c = (c + 1) % 12
            display.show(Image.ALL_CLOCKS[c])
    
    return temp


def define_winner(p, ep):
    """Défnini le gagnant et affiche le résultat"""
    display.scroll("...")
    display.show(rps_images[ep])
    sleep(1500)
    if p == ep:
        display.scroll("Egalite !")
    elif (p == 0 and ep == 2) or (p == 1 and ep == 0) or (p == 2 and ep == 1):
        display.scroll("Gagne !")
    else:
        display.scroll("Perdu !")
    
    
def rps():
    """Rock Paper Scissors"""
    # Choix du joueur
    picked = choice()
    
    # Envoie du choix
    radio.send("CHOICE:" + str(picked))
    # Récupère le choix de l'adversaire
    e_picked = waiting_status(50, wait_ec, lambda ec: ec < 0)
    # Annonce la victoire / défaite
    define_winner(picked, e_picked)
    
    # Recommence la partie (?)
    display.show(rps_images["restart"])
    restart = False
    while True:
        if button_a.is_pressed():
            restart = False
            break
        elif button_b.is_pressed():
            restart = True
            break
    
    return restart


def main():
    c = select_canal()
    connect_to(c)
    running = True
    while running:
        running = rps()


if __name__ == '__main__':
    while True:
        main()
