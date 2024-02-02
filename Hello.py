# Importation des bibliothèques nécessaires
import streamlit as st
import pandas as pd
import math as mt
from scipy.integrate import odeint
import numpy as np
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)


def run():
    st.set_page_config(
        page_title="Livrable 3",
        page_icon="🚗",
    )


    progress_text = "Calcul en cours..."

    # Chargement des données depuis le fichier CSV
    data = pd.read_csv('caracteristiques_voitures.csv')

    # Mise en page de l'application Streamlit
    st.title("Calculateur de vitesse de voiture")

    st.image("circuit.png", caption='Shéma du circuit')
    st.divider()

    # Sélection du modèle de voiture à partir du fichier CSV
    modele_voiture = st.selectbox("Sélectionnez le modèle de voiture :", data['Nom'].tolist())

    # Affichage des caractéristiques du modèle sélectionné
    caracteristiques = data[data['Nom'] == modele_voiture].squeeze()
    st.subheader("▪ Caractéristiques du modèle sélectionné :")
    st.dataframe(caracteristiques, width=350)
    print(caracteristiques)
    st.divider()

    # Liste déroulante pour choisir la partie du circuit à simuler
    st.subheader("▪ Paramètres pour simuler une partie du circuit :")
    partie_circuit = st.selectbox("Sélectionnez la partie du circuit a simuler :", ["Pente", "Looping", "Ravin", "Fin de piste"])
    st.caption("Optionnel")
    v_inital = st.number_input("Choisir votre vitesse inital (en m/s) :", 0, 200, 20, 1, placeholder="Rentrez votre vitesse inital")
    st.caption("Optionnel")

    # Option pour choisir si l'on prend des accessoires
    st.divider()
    st.subheader("▪ Paramètres pour les accessoires :")
    utiliser_nos = st.toggle("Utiliser le NOS ?")
    if utiliser_nos:
        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            pass
        with col2:
            st.caption("Choisir seulement une seule option")
            nos_pente = st.checkbox("Pente")
            nos_looping = st.checkbox("Looping")
            nos_piste = st.checkbox("Piste")
        st.divider()
    else:
        nos_pente = False
        nos_looping = False
        nos_piste = False

    utiliser_ailerons = st.toggle("Utiliser le système de planage ?")

    # Option pour choisir si l'on prend les frottements en compte
    st.divider()
    st.subheader("▪ Choisir avec/sans frottements :")
    frottements = st.toggle("Faire avec frottements")

    # FONCTION :
    def vitesse_pente(g, masse, acceleration):
        OM = 0
        t = 0
        while OM < 31:
            OM = 0.5 * (g * mt.sin(mt.radians(3.699)) + acceleration ) * t**2
            t = t + 0.001
            #print(OM)
        #print(t)
        v = (g * mt.sin(mt.radians(3.699)) +  acceleration ) * t
        return v,t

    def vitesse_pente_frottement(g, masse, acceleration, l, L, h, Cx):
        v = 0
        t=0
        OM = 0
        dt = 0.00001
        Surface = L*h
        k = 0.5 * (1.225 * Surface * Cx)
        while OM < 31:
            v += (g * mt.sin(mt.radians(3.699)) + acceleration - ((k * v**2) / masse)  - (0.1 * (g * mt.sin(mt.radians(3.699)))) ) * dt
            # print (v, OM)
            OM += v * dt
            t += dt
        return v,t

    def systeme_equations(y, t, m, g, r, F):
        try:
            dydt = [y[1],
                    (-m * g * np.sin(y[0]) - 0.5 * (r * y[1] ** 2) - (r * (y[1] ** 2)) + F) / (m * r)]
        except OverflowError:
            dydt = y
        return dydt

    def vitesse_looping(g, masse, acceleration, v_initial):
        r = 6
        temps = 0
        theta_initial = 0.0
        theta_dot_initial = v_initial / r

        t = np.linspace(0, 5, 1000)

        solution = odeint(systeme_equations, [theta_initial, theta_dot_initial], t,
                          args=(masse, g, r, acceleration))

        theta = solution[:, 0]
        theta_dot = solution[:, 1]

        def tri(n):
            return n < 2 * mt.pi

        filtered_theta = list(filter(tri, theta))
        filtered_theta_dot = theta_dot[:len(filtered_theta)]

        temps = t[len(filtered_theta) - 1]
        vitesse = r * filtered_theta_dot

        data = {"Theta": filtered_theta, "Vitesse de la voiture": vitesse}
        df = pd.DataFrame(data)
        st.line_chart(df, x='Theta', y='Vitesse de la voiture',width=650)

        return vitesse[-1],temps

    def systeme_equations_frottement(y, t, m, g, r, Cx, rho, Sx, frot, F):
        try:
            dydt = [y[1],
                    (-m * g * np.sin(y[0]) - 0.5 * Cx * rho * Sx * (r * y[1] ** 2) - frot * (r * (y[1] ** 2)) + F) / (
                                m * r)]
        except OverflowError:
            dydt = y
        return dydt

    def vitesse_looping_frottement(g, masse, acceleration, v_initial, mu, rho, Cx, L, h):
        r = 6
        temps = 0
        Sx = L * h
        theta_initial = 0.0
        theta_dot_initial = v_initial / r

        t = np.linspace(0, 5, 1000)

        solution = odeint(systeme_equations_frottement, [theta_initial, theta_dot_initial], t,
                          args=(masse, g, r, Cx, rho, Sx, mu, acceleration))

        theta = solution[:, 0]
        theta_dot = solution[:, 1]

        def tri(n):
            return n < 2 * mt.pi

        filtered_theta = list(filter(tri, theta))
        filtered_theta_dot = theta_dot[:len(filtered_theta)]

        vitesse = r * filtered_theta_dot
        temps = t[len(filtered_theta)-1]

        data = {"Theta": filtered_theta, "Vitesse de la voiture": vitesse}
        df = pd.DataFrame(data)
        st.line_chart(df, x='Theta', y='Vitesse de la voiture',width=650)

        return vitesse[-1],temps

    def position_x(t,v_initial):
        v = v_initial * t
        return v

    def position_y(t):
        v = 0.5 *  -9.81 * t**2
        return v

    def graph_ravin(v_initial):
        if v_initial <=0:
            st.write("Ravin Impossible.")
            st.caption("Vitesse doit être supérieur à 0.")
            return 0,0
        temps = 0
        x=0
        y=0
        x_values = []
        y_values = []
        while x<9:
            x = position_x(temps, v_initial)
            y = position_y(temps)
            x_values.append(x)
            y_values.append(y)

            temps += 0.0001

        data = {"Longueur": x_values, "Hauteur": y_values}  # Inversez les rôles de x_values et y_values
        df = pd.DataFrame(data)
        st.scatter_chart(df, x='Longueur', y='Hauteur',width=650)

        return v_initial,temps

    def graph_ravin_frottement(v_initial, g , masse, l, L, h, Cx, Cz):
        if v_initial <=0:
            st.write("Ravin Impossible.")
            st.caption("Vitesse doit être supérieur à 0.")
            return 0,0
        temps = 0
        dt = 0.0001
        v_x = v_initial
        v_y = 0
        x=0
        y=1
        x_values = []
        y_values = []
        kx = (0.5 * (1.225 * l * h * Cx))
        ky = (0.5 * (1.225 * L * l * Cz))

        ay = -g

        while x<9:

            v_x -= (kx/masse) * (v_x**2) * dt
            v_y += ( ay - (ky/masse) * (v_y**2)) * dt

            x += v_x * dt
            y += v_y * dt
            # print(v_x,v_y)
            x_values.append(x)
            y_values.append(y)

            temps += dt

        data = {"Longueur": x_values, "Hauteur": y_values}  # Inversez les rôles de x_values et y_values
        df = pd.DataFrame(data)
        st.scatter_chart(df, x='Longueur', y='Hauteur',width=650)

        return v_x,temps

    def vitesse_piste(g, masse, acceleration, v_initial):
        OM = 0
        t = 0
        while OM < 10:
            OM = 0.5 * (acceleration) * t**2 + v_initial*t
            t = t + 0.0001
            #print(OM)
        #print(t)
        v = acceleration * t + v_initial
        return v,t

    def vitesse_piste_frottement(g, masse, acceleration, v_initial, l, L, h, Cx):
        v = v_initial
        t = 0
        OM = 0
        dt = 0.00001
        Surface = L * h
        k = 0.5 * (1.225 * Surface * Cx)
        while OM < 10:
            v += (acceleration - ((k * v**2) / masse)  - (0.1 * g) ) * dt
            OM += v * dt
            t += dt
            # print(v, OM)
        return v,t

    def calculer(caracteristiques):
        g = 9.81
        masse = int(caracteristiques[1])
        acceleration = float(caracteristiques[2])
        l = float(caracteristiques[3])
        L = float(caracteristiques[4])
        h = float(caracteristiques[5])
        Cx = float(caracteristiques[6])
        Cz = float(caracteristiques[7])
        print(g,masse,acceleration,l,L,h,Cx,Cz)
        st.divider()
        if partie_circuit == "Pente":
            if frottements == False :
                if nos_pente:
                    st.write("Le calcul de la vitesse à la fin de la pente")
                    v_pente,temps = vitesse_pente(g,masse,acceleration*1.3)
                    st.write(v_pente, "m/s")
                    st.write(temps, "s")
                    st.write("NOS Activé")
                else:
                    st.write("Le calcul de la vitesse à la fin de la pente")
                    v_pente,temps = vitesse_pente(g, masse, acceleration)
                    st.write(temps, "s")
                    st.write(v_pente, "m/s")
            else :
                if nos_pente:
                    st.write("Le calcul de la vitesse à la fin de la pente")
                    v_pente,temps = vitesse_pente_frottement(g,masse,acceleration*1.3,l,L,h,Cx)
                    st.write(v_pente, "m/s")
                    st.write(temps, "s")
                    st.write("NOS Activé")
                else:
                    st.write("Le calcul de la vitesse à la fin de la pente")
                    v_pente,temps = vitesse_pente_frottement(g, masse, acceleration,l,L,h,Cx)
                    st.write(v_pente, "m/s")
                    st.write(temps, "s")

        elif partie_circuit == "Looping":
            if frottements == False:
                if nos_looping:
                    st.write("Calcul Looping Avec Nos")
                    v_looping, temps = vitesse_looping(g, masse,acceleration, v_inital)
                    st.write(v_looping, "m/s")
                    st.write(temps, "s")
                else:
                    st.write("Calcul Looping Sans Nos")
                    v_looping, temps = vitesse_looping(g, masse, acceleration, v_inital)
                    st.write(v_looping, "m/s")
                    st.write(temps, "s")
            else:
                if nos_looping:
                    st.write("Calcul Looping Avec Nos")
                    v_looping, temps = vitesse_looping_frottement(g, masse, acceleration, v_inital, 0.1, 1.225, Cx, L, h)
                    st.write(v_looping, "m/s")
                    st.write(temps, "s")
                else:
                    st.write("Calcul Looping Sans Nos")
                    v_looping, temps = vitesse_looping_frottement(g, masse, acceleration, v_inital, 0.1, 1.225, Cx, L, h)
                    st.write(v_looping, "m/s")
                    st.write(temps, "s")

        elif partie_circuit == "Ravin":
            if frottements==False:
                if utiliser_ailerons:
                    st.write("Trajectoire de la voiture :")
                    v_ravin,temps = graph_ravin(v_inital)
                    st.write(v_ravin, "m/s")
                    st.write(temps, "s")
                    st.write("NOS Activé")
                else:
                    st.write("Trajectoire de la voiture :")
                    v_ravin,temps = graph_ravin(v_inital)
                    st.write(v_ravin, "m/s")
                    st.write(temps, "s")
            else:
                if utiliser_ailerons:
                    st.write("Trajectoire de la voiture :")
                    v_ravin,temps = graph_ravin_frottement(v_inital, g, masse, l, L, h, Cx*0.95, Cz*1.1)
                    st.write(v_ravin, "m/s")
                    st.write(temps, "s")
                    st.write("NOS Activé")
                else:
                    st.write("Trajectoire de la voiture :")
                    v_ravin,temps = graph_ravin_frottement(v_inital, g, masse, l, L, h, Cx, Cz)
                    st.write(v_ravin, "m/s")
                    st.write(temps, "s")

        elif partie_circuit == "Fin de piste" :
            if frottements == False:
                if nos_piste:
                    st.write("Le temps total pour parcourir le circuit : ")
                    v_piste,temps = vitesse_piste(g, masse, acceleration*1.3, v_inital)
                    st.write(v_piste,"m/s")
                    st.write(temps, "s")
                    st.write ("NOS activé")
                else:
                    v_piste,temps = vitesse_piste(g, masse, acceleration, v_inital)
                    st.write(v_piste, "m/s")
                    st.write(temps, "s")
            else:
                if nos_piste:
                    st.write("Le temps total pour parcourir le circuit : ")
                    v_piste,temps = vitesse_piste_frottement(g,masse,acceleration*1.30,v_inital,l,L,h,Cx)
                    st.write(v_piste,"m/s")
                    st.write(temps, "s")
                    st.write ("NOS activé")
                else:
                    v_piste,temps = vitesse_piste_frottement(g,masse,acceleration,v_inital,l,L,h,Cx)
                    st.write(v_piste, "m/s")
                    st.write(temps, "s")

    def calculer_all(caracteristiques):
        g = 9.81
        masse = int(caracteristiques[1])
        acceleration = float(caracteristiques[2])
        l = float(caracteristiques[3])
        L = float(caracteristiques[4])
        h = float(caracteristiques[5])
        Cx = float(caracteristiques[6])
        Cz = float(caracteristiques[7])
        print(g,masse,acceleration,l,L,h,Cx,Cz)

        if nos_pente:
            acceleration_pente = acceleration*1.3
        else:
            acceleration_pente = acceleration
        if nos_looping:
            acceleration_looping = acceleration*1.3
        else:
            acceleration_looping = acceleration
        if nos_piste:
            acceleration_piste = acceleration*1.3
        else:
            acceleration_piste = acceleration
        if utiliser_ailerons:
            Cz = Cz * 1.1
            Cx = Cx * 0.95
            masse = masse+45

        if frottements:
            st.divider()
            my_bar.progress(25, text=progress_text)

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["① PENTE", "② LOOPING", "③ RAVIN", "④ PISTE", "⑤ RECAP"])

            with tab1:
                v_pente, temps_pente = vitesse_pente_frottement(g, masse, acceleration_pente, l, L, h, Cx)
                st.title("Pente :")
                st.write("Le calcul de la vitesse à la fin de la pente")
                st.write(round(v_pente, 2), "m/s")
                st.write("Chrono :")
                st.write(round(temps_pente, 2), "s")
                st.divider()
                st.image("Pente.png", caption='Schéma des forces dans la pente', width=650)
                st.caption("*Rappel des équations de mouvements :*")
                st.latex(r'''\overrightarrow{OM}_y = \frac{1}{2} \left(g \sin{\left(\alpha\right)} + a_m - \frac{\mu \cdot N - \frac{1}{2} \rho \cdot v^2 \cdot s \cdot C_x}{m}\right) t^2''')
                st.latex(r'''\overrightarrow{OM}_y = \frac{1}{2} \left(-g \cos{\left(\alpha\right)} + \frac{R}{m}\right) t^2''')

                my_bar.progress(50, text=progress_text)

            with tab2:
                r = 6   # Rayon du looping
                v_min_looping_A = mt.sqrt(2* g * (2*r)) #Vitesse minimal pour passer la pente du looping
                v_min_looping_B = mt.sqrt(g * r) #Vitesse minimal pour franchir le looping
                st.title("Looping :")
                st.caption("Tracé de la vitesse :")
                v_looping, temps_looping = vitesse_looping_frottement(g, masse, acceleration_looping, v_pente, 0.1, 1.225, Cx, L, h)

                col_A, col_B = st.columns([0.5, 0.5])
                with col_A:
                    st.write("Vitesse minimum pour passer la pente du looping :")
                    st.write(round(v_min_looping_A, 2), "m/s")
                    st.latex(r'''v_{\text{min}} = \sqrt{2g(h)}''')

                with col_B:
                    st.write("Vitesse minimum pour passer le looping en entier :")
                    st.write(round(v_min_looping_B, 2), "m/s")
                    st.latex(r'''v_{\text{min}} = \sqrt{g \cdot r}''')

                st.divider()
                st.metric("Vitesse à la fin du looping :", str(round(v_looping, 2)) + " m/s",
                          round(v_pente - v_min_looping_B, 2))
                if v_pente < v_min_looping_B:
                    st.write("Le looping est donc impossible")
                else:
                    st.write("Le looping est donc possible")
                st.write("Chrono :")
                st.write(round(temps_looping, 2), "s")

                st.divider()
                st.image("Looping.png", caption='Schéma des forces dans le looping', width=660)
                st.caption("*Rappel des équations de mouvements :*")
                st.latex(r'''\vec{OM} = r \vec{e}_r''')
                equa1, equa2 = st.columns([0.5, 0.5])
                with equa1:
                    st.latex(r'''\vec{e}_r = - r \dot{\theta}^2 = g \cos{\theta} - R''')
                with equa2:
                    st.latex(r'''\vec{e}_\theta = r \ddot{\theta} = mg \sin{\theta} + a_m - \frac{\mu N - \frac{1}{2} \rho v^2 s C_x}{m}''')

                my_bar.progress(75, text=progress_text)

            with tab3:
                v_min_ravin = 20
                st.title("Ravin :")
                st.caption("Trajectoire de la voiture :")
                v_ravin, temps_ravin = graph_ravin_frottement(v_looping,g,masse,l,L,h,Cx,Cz)
                st.write("Vitesse minimum pour passer le ravin :")
                st.write(round(v_min_ravin, 2), "m/s")
                st.metric("Vitesse à la fin du ravin", str(round(v_ravin, 2)) + "m/s", round(v_ravin - v_min_ravin, 2))
                if v_ravin < v_min_ravin:
                    st.write("Ravin est donc impossible")
                else:
                    st.write("Ravin est donc possible")
                st.write("Chrono :")
                st.write(round(temps_ravin, 2), "s")
                st.divider()
                st.image("Ravin.png", caption='Schéma des forces dans le ravin', width=650)
                st.caption("*Rappel des équations de mouvements :*")
                equa1, equa2 = st.columns([0.5, 0.5])
                with equa1:
                    st.latex(r'''\overrightarrow{OM}_x = \frac{1}{2} \left(-\frac{1}{2} \frac{\rho \cdot v^2 \cdot s \cdot C_x}{m}\right) t^2 + v_0 t''')
                with equa2:
                    st.latex(r'''\overrightarrow{OM}_y = \frac{1}{2} \left(-g + \frac{\rho \cdot v^2 \cdot s \cdot C_z}{m}\right) t^2''')

                my_bar.progress(100, text=progress_text)

            with tab4:
                v_piste, temps_piste = vitesse_piste_frottement(g,masse,acceleration_piste,v_ravin,l,L,h,Cx)
                st.title("Fin de piste :")
                st.write("Le calcul de la vitesse à la fin de la piste")
                st.write(round(v_piste, 2), "m/s")

                st.divider()
                st.image("Piste.png", caption='Schéma des forces dans la piste', width=650)
                st.caption("*Rappel des équations de mouvements :*")
                equa1, equa2 = st.columns([0.5, 0.5])
                with equa1:
                    st.latex(r'''\overrightarrow{OM}_x = \frac{1}{2} \left(-\frac{1}{2} \frac{\rho \cdot v^2 \cdot s \cdot C_x}{m}\right) t + v_0 t''')
                with equa2:
                    st.latex(r'''\overrightarrow{OM}_y = \frac{1}{2} \left(-g + \frac{\rho \cdot v^2 \cdot s \cdot C_z}{m}\right) t^2''')

                my_bar.empty()

            with tab5:
                temps_total = temps_pente+temps_looping+temps_ravin+temps_piste
                st.write("Chrono pour tout le circuit :")
                st.write(round(temps_total, 3),"seconde(s)")
                st.divider()
                if temps_total < 8 and v_min_ravin < v_looping and v_min_looping_B < v_pente:
                    st.subheader("RECORD BATTU !")
                    st.image("https://forums.pixeltailgames.com/uploads/default/original/3X/d/1/d12d0941862841dad6ffe2281b25aeb8d971f3b0.gif")
                elif v_min_ravin > v_looping or v_min_looping_B > v_pente :
                    st.subheader("C'EST LE CRASH !")
                    st.image("https://pa1.aminoapps.com/6825/e33c02e435883599bace42ae25b1e1bbf4cacdb5_hq.gif")
                    st.image("https://i.gifer.com/SqwX.gif")
                else:
                    st.subheader("RECORD RATÉ !")
                    st.image("https://media1.tenor.com/m/fVtFN_1f1HkAAAAC/mario-kart.gif")
                st.divider()
                st.header("◇ Récapitulatif des vitesses")

                v1, v2 = st.columns([0.5,0.5])
                with v1:
                    st.subheader("Vitesse en m/s")
                    st.write("› Vitesse pente :", round(v_pente,2), "m/s")
                    st.write("› Vitesse looping :", round(v_looping,2), "m/s")
                    st.write("› Vitesse ravin :", round(v_ravin,2), "m/s")
                    st.write("› Vitesse piste :", round(v_piste,2), "m/s")
                with v2:
                    st.subheader("Vitesse en km/h")
                    st.write("› Vitesse pente :", round(v_pente*3.6,2), "km/h")
                    st.write("› Vitesse looping :", round(v_looping*3.6,2), "km/h")
                    st.write("› Vitesse ravin :", round(v_ravin*3.6,2), "km/h")
                    st.write("› Vitesse piste :", round(v_piste*3.6,2), "km/h")

        else:
            st.divider()
            my_bar.progress(25, text=progress_text)

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["① PENTE", "② LOOPING", "③ RAVIN", "④ PISTE", "⑤ RECAP"])

            with tab1:
                v_pente,temps_pente = vitesse_pente(g,masse,acceleration_pente)
                st.title("Pente :")
                st.write("Le calcul de la vitesse à la fin de la pente")
                st.write(round(v_pente, 2), "m/s")
                st.write("Chrono :")
                st.write(round(temps_pente, 2), "s")
                st.divider()
                st.image("Pente.png", caption='Schéma des forces dans la pente', width=650)
                st.caption("*Rappel des équations de mouvements :*")
                equa1, equa2 = st.columns([0.5,0.5])
                with equa1:
                    st.latex(r'''\overrightarrow{OM}_x = \frac{1}{2} \left(g \sin{\left(\alpha\right)} + a_m\right) t^2''')
                with equa2:
                    st.latex(r'''\overrightarrow{OM}_y = \frac{1}{2} \left(-g \cos{\left(\alpha\right)} + \frac{R}{m}\right) t^2''')
                my_bar.progress(50, text=progress_text)

            with tab2:
                r = 6  # Rayon du looping
                v_min_looping_A = mt.sqrt(2 * g * (2*r))  # Vitesse minimal pour passer la pente du looping
                v_min_looping_B = mt.sqrt(g * r)  # Vitesse minimal pour franchir le looping
                st.title("Looping :")
                st.caption("Tracé de la vitesse :")
                v_looping, temps_looping = vitesse_looping(g, masse, acceleration_looping, v_pente)

                col_A, col_B = st.columns([0.5, 0.5])
                with col_A:
                    st.write("Vitesse minimum pour passer la pente du looping :")
                    st.write(round(v_min_looping_A, 2), "m/s")
                    st.latex(r'''v_{\text{min}} = \sqrt{2g(h)}''')

                with col_B:
                    st.write("Vitesse minimum pour passer le looping en entier :")
                    st.write(round(v_min_looping_B, 2), "m/s")
                    st.latex(r'''v_{\text{min}} = \sqrt{g \cdot r}''')

                st.divider()
                st.metric("Vitesse à la fin du looping :", str(round(v_looping,2)) + " m/s", round(v_pente-v_min_looping_B,2))
                if v_pente < v_min_looping_B:
                    st.write("Le looping est donc impossible")
                else:
                    st.write("Le looping est donc possible")
                st.write("Chrono :")
                st.write(round(temps_looping, 2), "s")

                st.divider()
                st.image("Looping.png", caption='Schéma des forces dans le looping', width=660)
                st.caption("*Rappel des équations de mouvements :*")
                st.latex(r'''\vec{OM} = r \vec{e}_r''')
                equa1, equa2 = st.columns([0.5, 0.5])
                with equa1:
                    st.latex(r'''\vec{e}_r = - r \dot{\theta}^2 = g \cos{\theta} - R''')
                with equa2:
                    st.latex(r'''\vec{e}_\theta = r \ddot{\theta} = g \sin{\theta} + a_m''')

                my_bar.progress(75, text=progress_text)

            with tab3:
                v_min_ravin = 20
                st.title("Ravin :")
                st.caption("Trajectoire de la voiture :")
                v_ravin, temps_ravin = graph_ravin(v_looping)
                st.write("Vitesse minimum pour passer le ravin :")
                st.write(round(v_min_ravin, 2), "m/s")
                st.metric("Vitesse à la fin du ravin", str(round(v_ravin,2)) + "m/s", round(v_ravin-v_min_ravin, 2))
                if v_ravin<v_min_ravin:
                    st.write("Ravin est donc impossible")
                else:
                    st.write("Ravin est donc possible")
                st.write("Chrono :")
                st.write(round(temps_ravin, 2), "s")
                st.divider()
                st.image("Ravin.png", caption='Schéma des forces dans le ravin', width=650)
                st.caption("*Rappel des équations de mouvements :*")
                equa1, equa2 = st.columns([0.5,0.5])
                with equa1:
                    st.latex(r'''\overrightarrow{OM}_x = V_0 t''')
                with equa2:
                    st.latex(r'''\overrightarrow{OM}_y = \frac{1}{2} \left(-g\right) t^2''')

                my_bar.progress(100, text=progress_text)

            with tab4:
                v_piste, temps_piste = vitesse_piste(g,masse,acceleration_piste,v_ravin)
                st.title("Fin de piste :")
                st.write("Le calcul de la vitesse à la fin de la piste")
                st.write(round(v_piste, 2), "m/s")

                st.divider()
                st.image("Piste.png", caption='Schéma des forces dans la piste', width=650)
                st.caption("*Rappel des équations de mouvements :*")
                equa1, equa2 = st.columns([0.5, 0.5])
                with equa1:
                    st.latex(r'''\overrightarrow{OM}_x = \frac{1}{2} a_m t^2 + V_0 t''')
                with equa2:
                    st.latex(r'''\overrightarrow{OM}_y = \frac{1}{2} \left(-g + \frac{R}{m}\right) t^2''')
                my_bar.empty()

            with tab5:
                temps_total = temps_pente+temps_looping+temps_ravin+temps_piste
                st.write("Chrono pour tout le circuit :")
                st.write(round(temps_total, 3),"seconde(s)")
                st.divider()
                if temps_total < 8 and v_min_ravin < v_looping and v_min_looping_B < v_pente:
                    st.subheader("RECORD BATTU !")
                    st.image("https://forums.pixeltailgames.com/uploads/default/original/3X/d/1/d12d0941862841dad6ffe2281b25aeb8d971f3b0.gif")
                elif v_min_ravin > v_looping or v_min_looping_B > v_pente :
                    st.subheader("C'EST LE CRASH !")
                    st.image("https://pa1.aminoapps.com/6825/e33c02e435883599bace42ae25b1e1bbf4cacdb5_hq.gif")
                    st.image("https://i.gifer.com/SqwX.gif")
                else:
                    st.subheader("RECORD RATÉ !")
                    st.image("https://media1.tenor.com/m/fVtFN_1f1HkAAAAC/mario-kart.gif")
                st.divider()
                st.header("◇ Récapitulatif des vitesses")

                v1, v2 = st.columns([0.5,0.5])
                with v1:
                    st.subheader("Vitesse en m/s")
                    st.write("› Vitesse pente :", round(v_pente,2), "m/s")
                    st.write("› Vitesse looping :", round(v_looping,2), "m/s")
                    st.write("› Vitesse ravin :", round(v_ravin,2), "m/s")
                    st.write("› Vitesse piste :", round(v_piste,2), "m/s")
                with v2:
                    st.subheader("Vitesse en km/h")
                    st.write("› Vitesse pente :", round(v_pente*3.6,2), "km/h")
                    st.write("› Vitesse looping :", round(v_looping*3.6,2), "km/h")
                    st.write("› Vitesse ravin :", round(v_ravin*3.6,2), "km/h")
                    st.write("› Vitesse piste :", round(v_piste*3.6,2), "km/h")

    my_bar = st.progress(0, text=progress_text)
    my_bar.empty()

    # Bouton pour effectuer le calcul
    if st.button("CALCULER partie circuit"):
        calculer(caracteristiques)

    if st.button("CALCULER CIRCUIT tout le circuit"):
        calculer_all(caracteristiques)


if __name__ == "__main__":
    run()
