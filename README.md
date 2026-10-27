# Resoftwa-AgenticAI
*&---------------------------------------------------------------------*
*& Report ZSHN_PO_OPEN_LIST
*&---------------------------------------------------------------------*
*& RICEFW Code       : Task - 02.
*& Author            : Sri Harsha Nelluri.
*& Developer         : C-NRAO.
*& Date              : 10/27/2026(MM/DD/YYYY).
*& Transport Request : Local Object.
*& Desription        : PO Open List.
*&---------------------------------------------------------------------*
REPORT zshn_po_open_list.

CLASS lcl_po DEFINITION.
  PUBLIC SECTION.
    METHODS get_data.
  PRIVATE SECTION.
    METHODS alv_report.
ENDCLASS.
TYPES: BEGIN OF ty_po,
         ebeln TYPE ekko-ebeln,
         ebelp TYPE ekpo-ebelp,
         bukrs TYPE ekko-bukrs,
         bstyp TYPE ekko-bstyp,
         bsart TYPE ekko-bsart,
         bsakz TYPE ekko-bsakz,
         loekz TYPE ekko-loekz,
         ekorg TYPE ekko-ekorg,
         matnr TYPE ekpo-matnr,
         menge TYPE ekpo-menge,
         meins TYPE ekpo-meins,
       END OF ty_po.
DATA: gt_po    TYPE TABLE OF ty_po.
DATA: gv_ebeln TYPE ebeln,
      go_salv  TYPE REF TO cl_salv_table,
      go_po    TYPE REF TO lcl_po.
SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
  SELECT-OPTIONS s_ebeln FOR gv_ebeln.
SELECTION-SCREEN END OF BLOCK b1.
CLASS lcl_po IMPLEMENTATION.
  METHOD get_data.
    SELECT a~ebeln,
           ebelp,
           a~bukrs,
           a~bstyp,
           bsart,
           bsakz,
           a~loekz,
           ekorg,
           matnr,
           menge,
           meins FROM ekko AS a
                 INNER JOIN ekpo AS b
                 ON b~ebeln = a~ebeln
                 INTO TABLE @gt_po
                 WHERE a~ebeln IN @s_ebeln
                 AND a~loekz = @space
                 AND elikz = @space.
    IF sy-subrc EQ 0.
      go_po->alv_report( ).
    ENDIF.
  ENDMETHOD.
  METHOD alv_report.
    DATA: lo_col_tab  TYPE REF TO cl_salv_column_table,
          lo_cols_tab TYPE REF TO cl_salv_columns_table.
    TRY.
        CALL METHOD cl_salv_table=>factory
          IMPORTING
            r_salv_table = go_salv
          CHANGING
            t_table      = gt_po.
      CATCH cx_salv_msg.
    ENDTRY.
    IF go_salv IS BOUND.
      go_salv->get_functions( )->set_all( abap_true ).
      go_salv->get_columns( )->set_optimize( abap_true ).
      go_salv->set_screen_status( report = 'ZSHN_PO_OPEN_LIST' pfstatus = 'ZSHN_PO_PFSTATUS' ).
      lo_cols_tab = go_salv->get_columns( ).
      IF lo_cols_tab IS BOUND.
        TRY.
            lo_col_tab ?= lo_cols_tab->get_column( 'EBELN' ).
          CATCH cx_salv_not_found.
        ENDTRY.
        lo_col_tab->set_key( abap_true ).
        TRY.
            lo_col_tab ?= lo_cols_tab->get_column( 'EBELP' ).
          CATCH cx_salv_not_found.
        ENDTRY.
        lo_col_tab->set_key( abap_true ).
      ENDIF.
    ENDIF.
  ENDMETHOD.
ENDCLASS.

START-OF-SELECTION.
  CREATE OBJECT go_po.
  go_po->get_data( ).

END-OF-SELECTION.
  IF go_salv IS BOUND.
    go_salv->display( ).
  ENDIF.
