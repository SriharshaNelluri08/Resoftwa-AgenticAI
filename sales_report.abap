*&---------------------------------------------------------------------*
*& Report ZSHN_SALES_ORDER_DATA
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT zshn_sales_order_data.

TYPES: BEGIN OF ty_final,
         vbeln  TYPE vbak-vbeln,
         auart  TYPE vbak-auart,
         netwr  TYPE vbak-netwr,
         waerk  TYPE vbak-waerk,
         vkorg  TYPE vbak-vkorg,
         vtweg  TYPE vbak-vtweg,
         spart  TYPE vbak-spart,
         posnr  TYPE vbap-posnr,
         matnr  TYPE vbap-matnr,
         kwmeng TYPE vbap-kwmeng,
         vrkme  TYPE vbap-vrkme,
       END OF ty_final.

DATA: gt_final TYPE STANDARD TABLE OF ty_final,
      gw_final TYPE ty_final.

SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
  SELECT-OPTIONS s_vbeln FOR gw_final-vbeln.
SELECTION-SCREEN END OF BLOCK b1.

START-OF-SELECTION.

  SELECT a~vbeln
         a~auart
         a~netwr
         a~waerk
         a~vkorg
         a~vtweg
         a~spart
         b~posnr
         b~matnr
         b~kwmeng
         b~vrkme FROM vbak AS a
               INNER JOIN vbap AS b
               ON b~vbeln = a~vbeln
               INTO TABLE gt_final
               WHERE a~vbeln IN s_vbeln.
  TRY.
      cl_salv_table=>factory( IMPORTING r_salv_table = DATA(go_salv) CHANGING t_table =  gt_final ).
    CATCH cx_salv_msg.
  ENDTRY.
  IF go_salv is bound.
    go_salv->get_columns( )->set_optimize( abap_true ).
    go_salv->get_functions( )->set_all( abap_true ).
    go_salv->display( ).
  ENDIF.
