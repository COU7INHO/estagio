import streamlit as st
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
from fpdf import FPDF
from datetime import datetime

page_icon = Image.open('icon_img.png')

st.set_page_config(
    page_title="Gait Analysis Software",
    layout="centered",
    page_icon=page_icon,
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'Software para relaizar a análise dos desvios da marcha em amputados do membro infeior'
    }
)

with st.sidebar:
    files = []
    path = st.file_uploader('Carregar ficheiros', accept_multiple_files=True,
                            help='Carregar os ficheiros obtidos no Kinovea')
    for uploaded_file in path:
        files.append(pd.read_csv(uploaded_file, sep=';', decimal=','))
    if path:
        left_leg_h = files[0]
        right_leg_h = files[1]
        left_leg_v = files[2]
        right_leg_v = files[3]
        try:
            frontal_h = files[4]
            frontal_v = files[5]
        except IndexError:
            pass

def organize(file_horizontal, file_vertical):
    file_vertical.drop('Time (ms)', axis=1, inplace=True)
    file_horizontal.columns += "_H"
    file_horizontal.rename(columns=({"Time (ms)_H": "Time (ms)"}), inplace=True)
    file_vertical.columns += "_V"
    merged_data = pd.concat([file_horizontal, file_vertical], axis=1)
    return merged_data

def convert_scale(file):
    n_rows = file['Time (ms)'].count() - 1
    x_scale = np.arange(0, 100 + 100 / n_rows, 100 / n_rows)
    return x_scale

if path:
    merged = organize(right_leg_h, right_leg_v)
    merged_2 = organize(left_leg_h, left_leg_v)

    freq_right = convert_scale(merged)
    freq_left = convert_scale(merged_2)
    try:
        merged_frontal = organize(frontal_h, frontal_v)
        freq_frontal = convert_scale(merged_frontal)
    except NameError:
        pass

    if len(merged) != len(freq_right):
        freq_right = freq_right[: -1]

    if len(merged_2) != len(freq_left):
        freq_left = freq_left[: -1]

def angle_calculation(file):
    global distance

    alpha = np.arctan((file['GT_H'] - file['LE_H']) / (file['GT_V'] - file['LE_V']))
    y = int(distance) * np.cos(alpha) + file['GT_V']
    x = int(distance) * np.sin(alpha) + file['GT_H']

    trunk_angle = np.degrees(np.arctan(((x - file['A_H']) / (y - file['A_V']))))
    thigh_angle = np.degrees(np.arctan((file['LE_V'] - file['GT_V']) / (file['LE_H'] - file['GT_H'])))
    shank_angle = np.degrees(np.arctan((file['LM_V'] - file['LE_V']) / (file['LM_H'] - file['LE_H'])))
    foot_angle = np.degrees(np.arctan((file['VM_V'] - file['LM_V']) / (file['VM_H'] - file['LM_H'])))

    thigh_angle[thigh_angle <= 0] = thigh_angle[thigh_angle <= 0] + 180
    shank_angle[shank_angle <= 0] = shank_angle[shank_angle <= 0] + 180
    foot_angle[foot_angle >= 0] = 90 - foot_angle[foot_angle >= 0]
    foot_angle[foot_angle <= 0] = foot_angle[foot_angle <= 0] + 90

    hip_ang = thigh_angle - trunk_angle - 90
    knee_ang = thigh_angle - shank_angle
    ankle_ang = foot_angle - shank_angle + 90
    ankle_ang = ankle_ang - ankle_ang[0]

    return hip_ang, knee_ang, ankle_ang

def sub_plotting(x, y, title, ax=None, xlabel='Fase da marcha (%)', ylabel=''):
    if ax is None:
        ax = plt.gca()
    plot = ax.plot(x, y, linewidth=2, color='black')
    ax.set_xticks(np.arange(0, int(max(x) + max(x) * 0.1), int((max(x) / 10))))
    ax.set_xlabel(xlabel, fontsize=16)
    ax.margins(0, 0)
    ax.set_ylabel(ylabel, fontsize=16)
    ax.set_title(title, fontsize=18)
    ax.grid(True)
    return plot

def detect_marker(marker_name, file):
    if marker_name not in file.columns:
        marker = False
        st.warning('O marcador {} não está disponivel para ser analisado. \n Certifique-se que: \n - '
                 'Utilizou este marcador na recolha de dados \n - Atribui o nome correto ao marcador, '
                 '{}'.format(marker_name[:-2], marker_name[:-2]))
        return marker

def detect_marker_2(marker_name, file):
    if marker_name not in file.columns:
        marker = False
        pass
        return marker

def legs_comparasion(file_right, file_left, marker_H, marker_V):
    right_v = max(file_right[marker_V]) - min(file_right[marker_V])
    right_h = max(file_right[marker_H]) - min(file_right[marker_H])
    left_v = max(file_left[marker_V]) - min(file_left[marker_V])
    left_h = max(file_left[marker_H]) - min(file_left[marker_H])
    diff_v = abs(right_v - left_v)
    diff_h = abs(right_h - left_h)
    return right_h, right_v, left_h, left_v, diff_h, diff_v

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def inflection_point(freq_file, file, lower_lim, upper_lim, angle):
    hip_angle, knee_angle, ankle_angle = angle_calculation(file)

    if angle == 1:
        angle = hip_angle
    elif angle == 2:
        angle = knee_angle
    elif angle == 3:
        angle = ankle_angle

    lower_limit = find_nearest(freq_file, lower_lim)
    upper_limit = find_nearest(freq_file, upper_lim)

    lower_limit_index = int(np.transpose(np.nonzero(freq_file == lower_limit)))
    upper_limit_index = int(np.transpose(np.nonzero(freq_file == upper_limit)))

    derivative2 = np.gradient(np.gradient(angle))

    inflection = np.where(np.diff(np.sign(derivative2)))[0]

    i_point = []
    for i in range(len(inflection)):
        if inflection[i] > lower_limit_index and inflection[i] < upper_limit_index:
            i_point.append(inflection[i])
            ii_point = i_point[0]
            iii_point = ii_point * 100 / len(angle)

    return angle, iii_point, ii_point

def stance_phase(freq_file, file, lower_lim, upper_lim):
    global fps_rate
    _, _, inf_point = inflection_point(freq_file, file, lower_lim, upper_lim, 2)
    duration = inf_point / fps_rate
    return duration

def import_data(file_name):
    file = pd.read_csv(file_name, sep=';', decimal=',')
    return file

def markers_dif(file, marker1_H,marker1_V, marker2_H, marker2_V):
    L_H = max(file[marker1_H]) - min(file[marker1_H])
    R_H = max(file[marker2_H]) - min(file[marker2_H])
    diff_H = abs(L_H - R_H)
    L_V = max(file[marker1_V]) - min(file[marker1_V])
    R_V = max(file[marker2_V]) - min(file[marker2_V])
    diff_V = abs(L_V - R_V)
    return L_H, R_H, diff_H, L_V, R_V, diff_V

def create_pdf(img1, img2, img3, file_name):

    global name

    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()

    pdf.image('logo.png', x=10, y=20, w=65, h=37)
    pdf.set_font('times', 'B', 22)
    pdf.set_xy(65, 30)
    pdf.multi_cell(w=80, h=10, txt='Relatório \n Análise de marcha', border=0, align='c')
    data_hora = datetime.now()
    data_hora = data_hora.strftime("%d/%m/%Y")
    pdf.set_xy(150, 30)
    pdf.set_font('times', '', 12)
    pdf.cell(w=22, h=8, txt=data_hora, border=1)
    pdf.line(30, 60, 173, 60)

    pdf.set_xy(30, 65)
    pdf.set_font('times', 'B', 12)
    pdf.cell(w=30, txt='Nome: ')
    pdf.set_x(45)
    pdf.set_font('times', '', 12)
    pdf.cell(w=30, txt=name)

    pdf.set_xy(30, 71)
    pdf.set_font('times', 'B', 12)
    pdf.cell(w=30, txt='Nível de amputação: ')
    pdf.set_x(70)
    pdf.set_font('times', '', 12)
    pdf.cell(w=30, txt=amputation_level)

    pdf.set_xy(30, 77)
    pdf.set_font('times', 'B', 12)
    pdf.cell(w=30, txt='Perna amputada: ')
    pdf.set_x(63)
    pdf.set_font('times', '', 12)
    pdf.cell(w=30, txt=amputated_leg)

    pdf.set_xy(20, 83)
    pdf.image(img1, w=170, h=65)

    pdf.set_xy(20, 145)
    pdf.image(img2, w=170, h=65)

    pdf.set_xy(20, 206)
    pdf.image(img3, w=170, h=65)

    if comments !='':
        pdf.add_page()
        pdf.set_xy(30, 30)
        pdf.set_font('times', 'B', 14)
        pdf.cell(w=40, txt='Comentários')
        pdf.set_xy(30, 38)
        pdf.set_font('times', '', 12)
        pdf.multi_cell(w=145, txt=comments, border=1)

    pdf.output(file_name)

def hip_angle():
    fig1, (ax1, ax2) = plt.subplots(1, 2)

    hip_angle, _, _ = angle_calculation(merged)
    hip_angle_2, _, _ = angle_calculation(merged_2)

    sub_plotting(freq_left, hip_angle_2, 'Ângulo da anca - Perna esquerda', ax1)
    sub_plotting(freq_right, hip_angle, 'Ângulo da anca - Perna direita', ax2)
    ax1.set_xlabel('Fase da marcha (%)')
    ax2.set_xlabel('Fase da marcha (%)')
    ax1.set_ylabel('Ângulo (graus)')
    ax2.set_ylabel('Ângulo (graus)')
    ax1.set_xticks(np.arange(0, 110, step=10))
    ax2.set_xticks(np.arange(0, 110, step=10))
    ax1.set_ylim([-25, 45])
    ax2.set_ylim([-25, 45])

    ax1.text(1, -6, 'Flexão', fontsize=14)
    ax1.text(1, -8.5, 'Extensão', fontsize=14)
    ax1.arrow(17, -6, 0, 2, width=0.07, color='black', head_width=0.6)
    ax1.arrow(17, -7, 0, -2, width=0.07, color='black', head_width=0.6)

    ax2.text(1, -6, 'Flexão', fontsize=14)
    ax2.text(1, -8.5, 'Extensão', fontsize=14)
    ax2.arrow(17, -6, 0, 2, width=0.07, color='black', head_width=0.6)
    ax2.arrow(17, -7, 0, -2, width=0.07, color='black', head_width=0.6)

    ax1.axhline(0, color='gray', linewidth=1.5)
    ax2.axhline(0, color='gray', linewidth=1.5)

    ax1.set_aspect('auto')
    ax2.set_aspect('auto')

    fig1.set_figheight(8)
    fig1.set_figwidth(18)

    return fig1

def ankle_angle():
    fig3, (ax1, ax2) = plt.subplots(1, 2)

    _, _, ankle_angle = angle_calculation(merged)
    _, _, ankle_angle_2 = angle_calculation(merged_2)

    sub_plotting(freq_left, ankle_angle_2, 'Ângulo do tornozel - Perna esquerda', ax1)
    sub_plotting(freq_right, ankle_angle, 'Ângulo do tornozel - Perna direita', ax2)
    ax1.set_xlabel('Fase da marcha (%)')
    ax2.set_xlabel('Fase da marcha (%)')
    ax1.set_ylabel('Ângulo (graus)')
    ax2.set_ylabel('Ângulo (graus)')
    ax1.set_xticks(np.arange(0, 110, step=10))
    ax2.set_xticks(np.arange(0, 110, step=10))
    ax1.set_ylim([-20, 20])
    ax2.set_ylim([-20, 20])

    ax1.text(1, 15, 'Dorsiflexão', fontsize=14)
    ax1.text(1, 13, 'Flexão plantar', fontsize=14)
    ax1.arrow(24.5, 15, 0, 2, width=0.07, color='black', head_width=0.6)
    ax1.arrow(24.5, 14, 0, -2, width=0.07, color='black', head_width=0.6)

    ax2.text(1, 15, 'Dorsiflexão', fontsize=14)
    ax2.text(1, 13, 'Flexão plantar', fontsize=14)
    ax2.arrow(24.5, 15, 0, 2, width=0.07, color='black', head_width=0.6)
    ax2.arrow(24.5, 14, 0, -2, width=0.07, color='black', head_width=0.6)

    ax1.axhline(0, color='gray', linewidth=1.5)
    ax2.axhline(0, color='gray', linewidth=1.5)

    ax1.set_aspect('auto')
    ax2.set_aspect('auto')

    fig3.set_figheight(8)
    fig3.set_figwidth(18)

    return fig3

def sides_comparison():
    st.subheader('Resumo dos desvios da avalição de marcha')

    st.write('> **Desvios**')

    if detect_marker_2('A_H', merged) == False or detect_marker_2('A_H', merged_2) == False:
        pass
    else:
        r_h, r_v, l_h, l_v, diff_h, diff_v = legs_comparasion(merged, merged_2, 'A_H', 'A_V')
        if r_v > l_v:
            st.write('O ombro direito subiu mais %.4s cm' % diff_v)
        else:
            st.write('O ombro esquerdo subiu mais %.4s cm' % diff_v)

    if detect_marker_2('GT_H', merged) == False or detect_marker_2('GT_H', merged_2) == False:
        pass
    else:
        r_h, r_v, l_h, l_v, diff_h, diff_v = legs_comparasion(merged, merged_2, 'GT_H', 'GT_V')
        if r_v > l_v:
            st.write('O trocanter direito subiu mais %.4s cm' % diff_v)
        else:
            st.write('O trocanter esquerdo subiu mais %.4s cm' % diff_v)

    if detect_marker_2('LE_H', merged) == False or detect_marker_2('LE_H', merged_2) == False:
        pass
    else:
        r_h, r_v, l_h, l_v, diff_h, diff_v = legs_comparasion(merged, merged_2, 'LE_H', 'LE_V')
        if r_v > l_v:
            st.write('O joelho direito subiu mais %.4s cm' % diff_v)
        else:
            st.write('O joelho esquerdo subiu mais %.4s cm' % diff_v)

    if detect_marker_2('LM_H', merged) == False or detect_marker_2('LM_H', merged_2) == False:
        pass
    else:
        r_h, r_v, l_h, l_v, diff_h, diff_v = legs_comparasion(merged, merged_2, 'LM_H', 'LM_V')
        if r_v > l_v:
            st.write('O tornozelo direito subiu mais %.4s cm' % diff_v)
        else:
            st.write('O tornozelo esquerdo subiu mais %.4s cm' % diff_v)

    if detect_marker_2('VM_H', merged) == False or detect_marker_2('_H', merged_2) == False:
        pass
    else:
        r_h, r_v, l_h, l_v, diff_h, diff_v = legs_comparasion(merged, merged_2, 'VM_H', 'VM_V')
        if r_v > l_v:
            st.write('O pé direito subiu mais %.4s cm' % diff_v)
        else:
            st.write('O pé esquerdo subiu mais %.4s cm' % diff_v)

    st.write('> **Diferenças angulares**')

    _, knee_angle, _ = angle_calculation(merged)
    _, knee_angle_2, _ = angle_calculation(merged_2)

    if (max(knee_angle) - min(knee_angle)) > (max(knee_angle_2) - min(knee_angle_2)):
        st.write('O joelho direito teve uma amplitude de movimento de mais mais %.4sª'
                 % ((max(knee_angle) - min(knee_angle)) - (max(knee_angle_2) - min(knee_angle_2))))
    else:
        st.write('O joelho esquerdo teve uma amplitude de movimento de mais mais %.4sª'
                 % (max(knee_angle_2) - min(knee_angle_2)))

    _, _, ankle_angle = angle_calculation(merged)
    _, _, ankle_angle_2 = angle_calculation(merged_2)

    if max(ankle_angle) > max(ankle_angle_2):
        st.write('O pé direito teve mais %.4sª de dorsiflexão' % (max(ankle_angle) - max(ankle_angle_2)))
    else:
        st.write('O pé esquerdo teve mais %.4sª de dorsiflexão' % (max(ankle_angle_2) - max(ankle_angle)))

    if min(ankle_angle) < min(ankle_angle_2):
        st.write('O pé direito teve mais %.4sª de flexão plantar' % (abs(min(ankle_angle) - min(ankle_angle_2))))
    else:
        st.write('O pé esquerdo teve mais %.4sª de flexão plantar' % (
            abs(min(ankle_angle_2) - min(ankle_angle))))

    st.write(' > **Duração da fase de apoio** ')

    r_stance_phase_duration = stance_phase(freq_right, merged, min_lim_right_leg, 70)
    l_stance_phase_duration = stance_phase(freq_left, merged_2, min_lim_left_leg, 70)

    if r_stance_phase_duration > l_stance_phase_duration:
        st.write('A fase de apoio da perna direita, %.4ss, foi %.4s%% superior à da perna esquerda, %.4ss' % (
                r_stance_phase_duration, (r_stance_phase_duration - l_stance_phase_duration) / r_stance_phase_duration * 100,
                l_stance_phase_duration))
    else:
        st.write('A fase de apoio da perna esquerda, %.4ss, foi %.4s%% superior à da perna direita, %.4ss' % (
                l_stance_phase_duration, (l_stance_phase_duration - r_stance_phase_duration) / l_stance_phase_duration * 100,
                r_stance_phase_duration))

def img_comparison(file, freq):

    hip, knee, ankle = angle_calculation(file)
    _, i_point, _ = inflection_point(freq_right, merged, min_lim_right_leg, 70, 2)
    _, i_point_2, _ = inflection_point(freq_left, merged_2, min_lim_left_leg, 70, 2)

    if file is merged and freq is freq_right:
        inf_point = i_point

    if file is merged_2 and freq is freq_left:
        inf_point = i_point_2

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
    ax1.plot(freq, hip, color='black', linewidth=2.5)
    ax1.set_facecolor('#c7d2eb')
    ax1.tick_params('x', labelbottom=False)
    ax1.tick_params(labelsize=16)
    ax1.axhline(y=0, color='gray', linestyle='-')
    ax1.set_xticks(np.arange(0, 110, step=10))
    ax1.set_yticks(np.arange(-20, 45, step=10))
    ax2.plot(freq, knee - knee[0], color='black', linewidth=2.5)
    ax1.axvline(inf_point, color='black', linewidth=1.5)
    ax1.text(inf_point - 22, 34, 'Fase de apoio', fontsize=12, color='black')
    ax1.text(inf_point + 2, 34, 'Fase de balanço', fontsize=12, color='black')
    ax1.text(-2, -15, 'Anca', fontsize=18)
    ax2.set_facecolor('#c7d2eb')
    ax2.tick_params('x', labelbottom=False)
    ax2.tick_params(labelsize=16)
    ax2.axhline(y=0, color='gray', linestyle='-')
    ax2.set_ylabel('Ângulo (graus)', fontsize=18, fontweight='bold')
    ax2.set_xticks(np.arange(0, 110, step=10))
    ax2.set_yticks(np.arange(-10, 60, step=10))
    ax2.axvline(inf_point, color='black', linewidth=1.5)
    ax2.text(-2, 40, 'Joelho', fontsize=18)
    ax3.plot(freq, ankle, color='black', linewidth=2.5)
    ax3.set_facecolor('#c7d2eb')
    ax3.axhline(y=0, color='gray', linestyle='-')
    ax3.set_xlabel('Fase da marcha (%)', fontsize=18, fontweight='bold')
    ax3.set_xticks(np.arange(0, 110, step=10))
    ax3.set_yticks(np.arange(-20, 30, step=10))
    ax3.tick_params(labelsize=16)
    ax3.axvline(inf_point, color='black', linewidth=1.5)
    ax3.text(-2, -15, 'Tornozelo', fontsize=18)
    fig.set_figheight(10.65)
    fig.set_figwidth(8)
    st.pyplot(fig)

with st.container():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image('logo 1.png', width=550)

with st.sidebar:
    side_bar_title = st.header('Filtros')

with st.sidebar:
    amputation_level = st.radio(
        'Nível de amputação',
        ('Transtibial', 'Transfemoral'))

with st.sidebar:
    amputated_leg = st.radio(
        'Perna amputada',
        ('Direita', 'Esquerda'))

with st.sidebar:
    plane = st.radio(
        'Plano de movimento',
        ('Sagital', 'Frontal'))

with st.sidebar:
    distance = st.number_input('Distância ao trocânter', step=0.1,
                               help='Distância, em centímetros medida entre o marcador GT '
                                    'e a posição do trocânter. A distância deve ser a mesma nos dois membros.'
                                    ' Caso o marcador seja colocado exatamente em cima do '
                                    'trocânter este parâmetro deve manter-se igual a zero. ')

with st.sidebar:
    with st.expander('Definições avançadas'):
        fps_rate = st.number_input('Taxa de FPS', value=120, step=10,
                                   help='Taxa de FPS (Frames per second) usada durante a filmagem da marcha da pessoa')

        min_lim_right_leg = st.number_input('Início da fase de balanço (%) - Perna direita', value=55, step=1,
                                  help='Valor mínimo do intervalo onde ocorre a transição da fase de apoio'
                                       ' para a fase de balanço')

        min_lim_left_leg = st.number_input('Início da fase de balanço (%) - Perna esquerda', value=55, step=1,
                                            help='Valor mínimo do intervalo onde ocorre a transição da fase de apoio'
                                                 ' para a fase de balanço')

if plane == 'Sagital':

    with st.container():
        col1, col2 = st.columns([1.5, 1])
        with col1:
            option = st.selectbox('', ('Escolha um ângulo:', 'Anca', 'Joelho', 'Tornozelo'))
        summary = st.checkbox('Ver resumo da avaliação de marcha')
        comp_ref = st.checkbox('Comparar com a literatura')
        st.write('')

    with st.container():
        if path:

            if option == 'Escolha um ângulo':
                pass

            if option == 'Anca':
                with st.spinner('A processar os dados...'):

                    st.subheader('Ângulo da anca')

                    if detect_marker('A_H', merged) == False or detect_marker('GT_H', merged) == False or\
                            detect_marker('LE_H', merged) == False or detect_marker('A_H', merged_2) == False or\
                            detect_marker('GT_H', merged_2) == False or detect_marker('LE_H', merged_2) == False:
                        pass
                    else:
                        fig1 = hip_angle()
                        fig1.set_facecolor('#F5F5F5')
                        st.pyplot(fig1)

                        fig_name = 'Hip angle.png'
                        fig1.savefig(fig_name)

                        with open(fig_name, "rb") as f:
                            btn = st.download_button(
                                label="Descarregar imagem",
                                data=f,
                                file_name=fig_name,
                                mime="image/png")

            if option == 'Joelho':
                with st.spinner('A processar os dados...'):

                    st.subheader('Ângulo do joelho')

                    if detect_marker('GT_H', merged) == False or detect_marker('LE_H', merged) == False or \
                            detect_marker('LM_H', merged) == False or detect_marker('GT_H', merged_2) == False or \
                            detect_marker('LE_H', merged_2) == False or detect_marker('LM_H', merged_2) == False:
                        pass
                    else:
                        fig2, (ax1, ax2) = plt.subplots(1, 2)

                        knee_angle, i_point, _ = inflection_point(freq_right, merged, min_lim_right_leg, 70, 2)
                        knee_angle_2, i_point_2, _ = inflection_point(freq_left, merged_2, min_lim_left_leg, 70, 2)

                        sub_plotting(freq_left, knee_angle_2 - knee_angle_2[0], 'Ângulo do joelho - Perna esquerda', ax1)
                        sub_plotting(freq_right, knee_angle - knee_angle[0], 'Ângulo do joelho - Perna direita', ax2)
                        ax1.set_xlabel('Fase da marcha (%)')
                        ax2.set_xlabel('Fase da marcha (%)')
                        ax1.set_ylabel('Ângulo (graus)')
                        ax2.set_ylabel('Ângulo (graus)')
                        ax1.set_xticks(np.arange(0, 110, step=10))
                        ax2.set_xticks(np.arange(0, 110, step=10))
                        ax1.set_ylim([-10, 60])
                        ax2.set_ylim([-10, 60])

                        ax1.text(1, 40, 'Flexão', fontsize=14)
                        ax1.text(1, 37.5, 'Extensão', fontsize=14)
                        ax1.arrow(19.5, 40, 0, 2, width=0.07, color='black', head_width=0.6)
                        ax1.arrow(19.5, 39, 0, -2, width=0.07, color='black', head_width=0.6)

                        ax2.text(1, 40, 'Flexão', fontsize=14)
                        ax2.text(1, 37.5, 'Extensão', fontsize=14)
                        ax2.arrow(19.5, 40, 0, 2, width=0.07, color='black', head_width=0.6)
                        ax2.arrow(19.5, 39, 0, -2, width=0.07, color='black', head_width=0.6)

                        ax1.axhline(0, color='gray', linewidth=1.5)
                        ax2.axhline(0, color='gray', linewidth=1.5)

                        ax1.set_aspect('auto')
                        ax2.set_aspect('auto')

                        fig2.set_figheight(8)
                        fig2.set_figwidth(18)

                        fig2.set_facecolor('#F5F5F5')

                        check_box = st.checkbox('Ver fases da marcha')
                        if check_box:
                            ax1.axvline(i_point_2, color='red', linewidth=1.5)
                            ax2.axvline(i_point, color='red', linewidth=1.5)

                            ax1.text(i_point_2 - 22, 55, 'Fase de apoio', fontsize=12, color='black')
                            ax1.text(i_point_2 + 2, 55, 'Fase de balanço', fontsize=12, color='black')
                            ax2.text(i_point - 22, 55, 'Fase de apoio', fontsize=12, color='black')
                            ax2.text(i_point + 2, 55, 'Fase de balanço', fontsize=12, color='black')

                        st.pyplot(fig2)

                        fig = 'Knee angle.png'
                        plt.savefig(fig)
                        with open(fig, "rb") as f:
                            btn = st.download_button(
                                label="Descarregar imagem",
                                data=f,
                                file_name=fig,
                                mime="image/png")

            if option == 'Tornozelo':
                with st.spinner('A processar os dados...'):

                    st.subheader('Ângulo do tornozelo')

                    if detect_marker('LE_H', merged) == False or detect_marker('LM_H',merged) == False or\
                            detect_marker('VM_H', merged) == False or \
                            detect_marker('LE_H', merged_2) == False or detect_marker('LM_H', merged_2) == False or\
                            detect_marker('VM_H', merged_2) == False:
                        pass
                    else:
                        fig3 = ankle_angle()
                        fig3.set_facecolor('#F5F5F5')
                        st.pyplot(fig3)

                        fig_name = 'Ankle angle.png'
                        fig3.savefig(fig_name)

                        fig = 'Ankle angle.png'
                        plt.savefig(fig)
                        with open(fig, "rb") as f:
                            btn = st.download_button(
                                label="Descarregar imagem",
                                data=f,
                                file_name=fig,
                                mime="image/png")

            with col2:
                st.write('Relatório do utente')
                report_checkbox = st.checkbox('Gerar relatório')

            if report_checkbox:

                st.subheader('Relatório do utente')
                name = st.text_input('Nome do utente', value='')
                comments = st.text_area('Comentários', value='', help='Se desejar, adicione comentários'
                                                                      ' relativos à avaliaçao de marcha do utente')

                fig1 = hip_angle()
                fig_name1 = 'Hip angle.png'
                fig1.savefig(fig_name1)

                fig2, (ax1, ax2) = plt.subplots(1, 2)
                knee_angle, i_point, _ = inflection_point(freq_right, merged, min_lim_right_leg, 70, 2)
                knee_angle_2, i_point_2, _ = inflection_point(freq_left, merged_2, min_lim_left_leg, 70, 2)
                sub_plotting(freq_left, knee_angle_2 - knee_angle_2[0], 'Ângulo do joelho - Perna esquerda', ax1)
                sub_plotting(freq_right, knee_angle - knee_angle[0], 'Ângulo do joelho - Perna direita', ax2)
                ax1.set_xlabel('Fase da marcha (%)')
                ax2.set_xlabel('Fase da marcha (%)')
                ax1.set_ylabel('Ângulo (graus)')
                ax2.set_ylabel('Ângulo (graus)')
                ax1.set_xticks(np.arange(0, 110, step=10))
                ax2.set_xticks(np.arange(0, 110, step=10))
                ax1.set_ylim([-10, 60])
                ax2.set_ylim([-10, 60])
                ax1.text(1, 40, 'Flexão', fontsize=14)
                ax1.text(1, 37.5, 'Extensão', fontsize=14)
                ax1.arrow(19.5, 40, 0, 2, width=0.07, color='black', head_width=0.6)
                ax1.arrow(19.5, 38, 0, -2, width=0.07, color='black', head_width=0.6)
                ax2.text(1, 40, 'Flexão', fontsize=14)
                ax2.text(1, 37.5, 'Extensão', fontsize=14)
                ax2.arrow(19.5, 40, 0, 2, width=0.07, color='black', head_width=0.6)
                ax2.arrow(19.5, 38, 0, -2, width=0.07, color='black', head_width=0.6)
                ax1.set_aspect('auto')
                ax2.set_aspect('auto')
                fig2.set_figheight(8)
                fig2.set_figwidth(18)
                ax1.axvline(i_point_2, color='red', linewidth=1.5)
                ax2.axvline(i_point, color='red', linewidth=1.5)
                ax1.text(i_point_2 - 22, 55, 'Fase de apoio', fontsize=12, color='black')
                ax1.text(i_point_2 + 2, 55, 'Fase de balanço', fontsize=12, color='black')
                ax2.text(i_point - 22, 55, 'Fase de apoio', fontsize=12, color='black')
                ax2.text(i_point + 2, 55, 'Fase de balanço', fontsize=12, color='black')
                ax1.axhline(0, color='gray', linewidth=1.5)
                ax2.axhline(0, color='gray', linewidth=1.5)

                fig_name2 = 'Knee angle.png'
                fig2.savefig(fig_name2)

                fig3 = ankle_angle()
                fig_name3 = 'Ankle angle.png'
                fig3.savefig(fig_name3)

                pdf_name = 'Relatório.pdf'
                create_pdf(fig_name1, fig_name2, fig_name3, pdf_name)

                with open(pdf_name, 'rb') as pdf:
                    st.download_button(
                        label="Descarregar relatório",
                        data=pdf,
                        file_name=pdf_name,
                        mime="application/pdf",
                    )

    with st.container():

        if summary:
            if files == []:
                st.warning('O relatório não pode ser criado porque não foram carregados ficheiros para fazer a análise')
            else:
                sides_comparison()

    with st.container():

        if comp_ref:
            if files == []:
                st.warning('O relatório não pode ser criado porque não foram carregados ficheiros para fazer a análise')
            else:

                col1, col2 = st.columns([1.5, 1])
                with col1:
                    option_comp = st.selectbox('Escolha a perna que pretende analisar',
                                               {'Perna amputada', 'Perna intacta'}, index=0)

                col1, col2 = st.columns(2)
                if option_comp == 'Perna amputada':
                    if amputation_level == 'Transtibial' and amputated_leg == 'Direita':
                        with col1:
                            st.write('**Resultados**')
                            img_comparison(merged, freq_right)

                        with col2:
                            st.write('**Referência**')
                            st.image('bellow.png')
                            st.write('Referência: Whittle, M. (2014). Gait Analysis (4th ed., p. 132).'
                                     ' Burlington: Elsevier Science.')

                    if amputation_level == 'Transtibial' and amputated_leg == 'Esquerda':
                        with col1:
                            st.write('**Resultados**')
                            img_comparison(merged_2, freq_left)

                        with col2:
                            st.write('**Referência**')
                            st.image('bellow.png')
                            st.write('Referência: Whittle, M. (2014). Gait Analysis (4th ed., p. 132).'
                                     ' Burlington: Elsevier Science.')

                    if amputation_level == 'Transfemoral' and amputated_leg == 'Direita':
                        with col1:
                            st.write('**Resultados**')
                            img_comparison(merged, freq_right)

                        with col2:
                            st.write('**Referência**')
                            st.image('above.png')
                            st.write('Referência: Whittle, M. (2014). Gait Analysis (4th ed., p. 131).'
                                     ' Burlington: Elsevier Science.')

                    if amputation_level == 'Transfemoral' and amputated_leg == 'Esquerda':
                        with col1:
                            st.write('**Resultados**')
                            img_comparison(merged_2, freq_left)

                        with col2:
                            st.write('**Referência**')
                            st.image('above.png')
                            st.write('Referência: Whittle, M. (2014). Gait Analysis (4th ed., p. 131).'
                                     ' Burlington: Elsevier Science.')

                if option_comp == 'Perna intacta':
                    if amputated_leg == 'Direita':
                        with col1:
                            st.write('**Resultados**')
                            img_comparison(merged_2, freq_left)

                        with col2:
                            st.write('**Referência**')
                            st.image('normal.png')
                            st.write('Referência: Whittle, M. (2014). Gait Analysis (4th ed., p. 59).'
                                     ' Burlington: Elsevier Science.')

                    if amputated_leg == 'Esquerda':
                        with col1:
                            st.write('**Resultados**')
                            img_comparison(merged, freq_right)

                        with col2:
                            st.write('**Referência**')
                            st.image('normal.png')
                            st.write('Referência: Whittle, M. (2014). Gait Analysis (4th ed., p. 59).'
                                     ' Burlington: Elsevier Science.')


if plane == 'Frontal':
    with st.container():
        try:

            if detect_marker('LGT_H', merged_frontal) == False or detect_marker('RGT_H', merged_frontal) == False:
                pass
            else:
                st.subheader('Resumo dos desvios da avalição de marcha')

                L_H, R_H, dif_H, L_V, R_V, dif_V = markers_dif(merged_frontal, 'LGT_H', 'LGT_V', 'RGT_H', 'RGT_V')

                if L_H > R_H:
                    st.write('O marcador LGT movimentou-se mais %.4s cm do que o marcador RGT,'
                             ' na direção horizontal' % dif_H)
                else:
                    st.write('O marcador RGT movimentou-se mais %.4s cm do que o marcador LGT,'
                             ' na direção horizontal' % dif_H)

                if L_V > R_V:
                    st.write('O marcador LGT subiu mais %.4s cm do que o marcador RGT' % dif_V)
                else:
                    st.write('O marcador RGT subiu mais %.4s cm do que o marcador LGT' % dif_V)

            if detect_marker('LLE_H', merged_frontal) == False or detect_marker('RLE_H', merged_frontal) == False:
                pass
            else:
                L_H, R_H, dif_H, L_V, R_V, dif_V = markers_dif(merged_frontal, 'LLE_H', 'LLE_V', 'RLE_H', 'RLE_V')

                if L_H > R_H:
                    st.write('O marcador LLE teve uma rotação externa de maix %.4s cm' % dif_H)
                else:
                    st.write('O marcador RLE teve uma rotação interna de mais %.4s cm' % dif_H)

                if L_V > R_V:
                    st.write('O marcador LLE subiu mais %.4s cm do que o marcador RLE' % dif_V)
                else:
                    st.write('O marcador RLE subiu mais %.4s cm do que o marcador LLE' % dif_V)

            if detect_marker('LTT_H', merged_frontal) == False or detect_marker('RTT_H', merged_frontal) == False:
                pass
            else:
                L_H, R_H, dif_H, L_V, R_V, dif_V = markers_dif(merged_frontal, 'LTT_H', 'LTT_V', 'RTT_H', 'RTT_V')

                if L_H > R_H:
                    st.write('O marcador LTT teve uma rotação externa de mais %.4s cm' % dif_H)
                else:
                    st.write('O marcador RTT teve uma rotação interna de mais %.4s cm' % dif_H)

                if L_V > R_V:
                    st.write('O marcador LTT subiu mais %.4s cm do que o marcador RTT' % dif_V)
                else:
                    st.write('O marcador RTT subiu mais %.4s cm do que o marcador LTT' % dif_V)

            if detect_marker('LLM_H', merged_frontal) == False or detect_marker('RLM_H', merged_frontal) == False:
                pass
            else:
                L_H, R_H, dif_H, L_V, R_V, dif_V = markers_dif(merged_frontal, 'LLM_H', 'LLM_V', 'RLM_H', 'RLM_V')

                if L_H > R_H:
                    st.write('O marcador LLM teve uma rotação externa de maix %.4s cm' % dif_H)
                else:
                    st.write('O marcador RLM teve uma rotação interna de mais %.4s cm' % dif_H)

                if L_V > R_V:
                    st.write('O marcador LLM subiu mais %.4s cm do que o marcador RTT' % dif_V)
                else:
                    st.write('O marcador RLM subiu mais %.4s cm do que o marcador LTT' % dif_V)

            if detect_marker('LVM_H', merged_frontal) == False or detect_marker('RVM_H', merged_frontal) == False:
                pass
            else:
                L_H, R_H, dif_H, L_V, R_V, dif_V = markers_dif(merged_frontal, 'LVM_H', 'LVM_V', 'RVM_H', 'RVM_V')

                if L_H > R_H:
                    st.write('O marcador LVM teve uma rotação externa de mais %.4s cm' % dif_H)
                else:
                    st.write('O marcador RVM teve uma rotação externa de mais %.4s cm' % dif_H)

                if L_V > R_V:
                    st.write('O marcador LVM subiu mais %.4s cm' % dif_V)
                else:
                    st.write('O marcador RVM subiu mais %.4s cm do que o marcador LVM' % dif_V)
        except NameError:
            st.warning('O resumo não pode ser apresentado porque não existem ficheiros para analisar.'
                       ' \n \n Certifique-se que foram carregados os ficheiros relativos ao plano frontal')









