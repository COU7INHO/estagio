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
