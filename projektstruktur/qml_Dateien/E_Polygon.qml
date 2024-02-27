<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis readOnly="0" version="3.8.3-Zanzibar" styleCategories="LayerConfiguration|Fields|Forms">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <fieldConfiguration>
    <field name="id">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="messdatum">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option value="false" name="allow_null" type="bool"/>
            <Option value="true" name="calendar_popup" type="bool"/>
            <Option value="yyyy-MM-dd" name="display_format" type="QString"/>
            <Option value="yyyy-MM-dd" name="field_format" type="QString"/>
            <Option value="false" name="field_iso_format" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="aktcode">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="obj_type">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" name="AllowMulti" type="bool"/>
            <Option value="true" name="AllowNull" type="bool"/>
            <Option value="&quot;field_4&quot;  = '1' and  strpos(  &quot;field_5&quot; ,'Linie')>0" name="FilterExpression" type="QString"/>
            <Option value="field_1" name="Key" type="QString"/>
            <Option value="Objekttypen_c35b1304_9467_40b5_a815_1c0e889d43c7" name="Layer" type="QString"/>
            <Option value="Objekttypen" name="LayerName" type="QString"/>
            <Option value="delimitedtext" name="LayerProviderName" type="QString"/>
            <Option value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt_leer/Listen/Objekttypen.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes" name="LayerSource" type="QString"/>
            <Option value="1" name="NofColumns" type="int"/>
            <Option value="true" name="OrderByValue" type="bool"/>
            <Option value="false" name="UseCompleter" type="bool"/>
            <Option value="field_1" name="Value" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="obj_art">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" name="AllowMulti" type="bool"/>
            <Option value="true" name="AllowNull" type="bool"/>
            <Option value="strpos(  &quot;Field_2&quot; , concat( '|', current_value( 'obj_type' ),'|' ) ) > 0 and (&quot;Field_4&quot;  =  1)" name="FilterExpression" type="QString"/>
            <Option value="field_1" name="Key" type="QString"/>
            <Option value="Objektarten_affd5a69_af7f_405b_a1d1_7847ba634da5" name="Layer" type="QString"/>
            <Option value="Objektarten" name="LayerName" type="QString"/>
            <Option value="delimitedtext" name="LayerProviderName" type="QString"/>
            <Option value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt_leer/Listen/Objektarten.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes" name="LayerSource" type="QString"/>
            <Option value="1" name="NofColumns" type="int"/>
            <Option value="true" name="OrderByValue" type="bool"/>
            <Option value="false" name="UseCompleter" type="bool"/>
            <Option value="field_1" name="Value" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="schnitt_nr">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="planum">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="material">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" name="AllowMulti" type="bool"/>
            <Option value="true" name="AllowNull" type="bool"/>
            <Option value="strpos(  &quot;Field_2&quot; , concat( '|', current_value( 'obj_type' ),'|' ) ) > 0 and (&quot;Field_4&quot;  =  1)" name="FilterExpression" type="QString"/>
            <Option value="field_1" name="Key" type="QString"/>
            <Option value="Material_daa89ee4_3d9a_4002_83bb_b99d305ceeb6" name="Layer" type="QString"/>
            <Option value="Material" name="LayerName" type="QString"/>
            <Option value="delimitedtext" name="LayerProviderName" type="QString"/>
            <Option value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt_leer/Listen/Material.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes" name="LayerSource" type="QString"/>
            <Option value="1" name="NofColumns" type="int"/>
            <Option value="true" name="OrderByValue" type="bool"/>
            <Option value="false" name="UseCompleter" type="bool"/>
            <Option value="field_1" name="Value" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bef_nr">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="fund_nr">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geo-arch">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" name="AllowMulti" type="bool"/>
            <Option value="false" name="AllowNull" type="bool"/>
            <Option value="" name="FilterExpression" type="QString"/>
            <Option value="field_1" name="Key" type="QString"/>
            <Option value="geo_arch_d6d32e04_5d97_4afd_91a2_0df1add63c17" name="Layer" type="QString"/>
            <Option value="geo_arch" name="LayerName" type="QString"/>
            <Option value="delimitedtext" name="LayerProviderName" type="QString"/>
            <Option value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt/Listen/geo_arch.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes" name="LayerSource" type="QString"/>
            <Option value="1" name="NofColumns" type="int"/>
            <Option value="true" name="OrderByValue" type="bool"/>
            <Option value="false" name="UseCompleter" type="bool"/>
            <Option value="field_1" name="Value" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="zeit">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" name="AllowMulti" type="bool"/>
            <Option value="true" name="AllowNull" type="bool"/>
            <Option value=" &quot;field_7&quot;  = 1" name="FilterExpression" type="QString"/>
            <Option value="field_6" name="Key" type="QString"/>
            <Option value="Zeiten_6f689fbf_7fa7_4148_8480_fbf74ef1b317" name="Layer" type="QString"/>
            <Option value="Zeiten" name="LayerName" type="QString"/>
            <Option value="delimitedtext" name="LayerProviderName" type="QString"/>
            <Option value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt/Listen/Zeiten.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes" name="LayerSource" type="QString"/>
            <Option value="1" name="NofColumns" type="int"/>
            <Option value="false" name="OrderByValue" type="bool"/>
            <Option value="false" name="UseCompleter" type="bool"/>
            <Option value="field_6" name="Value" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="anz_rei">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="prob_nr">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="uuid">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" name="IsMultiline" type="bool"/>
            <Option value="false" name="UseHtml" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="id"/>
    <alias index="1" name="Aufnamedatum" field="messdatum"/>
    <alias index="2" name="Grabung" field="aktcode"/>
    <alias index="3" name="Objekttyp" field="obj_type"/>
    <alias index="4" name="Objektart" field="obj_art"/>
    <alias index="5" name="Schnitt-Nr" field="schnitt_nr"/>
    <alias index="6" name="Planum" field="planum"/>
    <alias index="7" name="Material" field="material"/>
    <alias index="8" name="Bemerkung" field="bemerkung"/>
    <alias index="9" name="Befund-Nr" field="bef_nr"/>
    <alias index="10" name="Fund-Nr" field="fund_nr"/>
    <alias index="11" name="Geo/Arch" field="geo-arch"/>
    <alias index="12" name="" field="zeit"/>
    <alias index="13" name="" field="anz_rei"/>
    <alias index="14" name="Probe-Nr" field="prob_nr"/>
    <alias index="15" name="" field="uuid"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" expression=" if (count( &quot;id&quot; )= 0 , 0, maximum( &quot;id&quot;)+1)" field="id"/>
    <default applyOnUpdate="0" expression=" now( )" field="messdatum"/>
    <default applyOnUpdate="0" expression=" @aktcode " field="aktcode"/>
    <default applyOnUpdate="0" expression="if( @autoAttribute = 'True',  @obj_type ,'' ) " field="obj_type"/>
    <default applyOnUpdate="0" expression=" if( @autoAttribute = 'True',  @obj_art ,'' ) " field="obj_art"/>
    <default applyOnUpdate="0" expression=" if( @autoAttribute = 'True',  @schnitt_nr ,'' ) " field="schnitt_nr"/>
    <default applyOnUpdate="0" expression=" if( @autoAttribute = 'True',  @planum ,'' ) " field="planum"/>
    <default applyOnUpdate="0" expression=" if( @autoAttribute = 'True',  @material ,'' ) " field="material"/>
    <default applyOnUpdate="0" expression="" field="bemerkung"/>
    <default applyOnUpdate="0" expression=" if( @autoAttribute = 'True',  @bef_nr ,'' ) " field="bef_nr"/>
    <default applyOnUpdate="0" expression=" if( @autoAttribute = 'True',  @fund_nr ,'' ) " field="fund_nr"/>
    <default applyOnUpdate="0" expression=" @arch-geo " field="geo-arch"/>
    <default applyOnUpdate="0" expression="" field="zeit"/>
    <default applyOnUpdate="0" expression="" field="anz_rei"/>
    <default applyOnUpdate="0" expression="" field="prob_nr"/>
    <default applyOnUpdate="0" expression="uuid()" field="uuid"/>
  </defaults>
  <constraints>
    <constraint notnull_strength="0" exp_strength="0" field="id" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="2" field="messdatum" constraints="4" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="aktcode" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="obj_type" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="obj_art" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="schnitt_nr" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="planum" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="material" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="bemerkung" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="bef_nr" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="fund_nr" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="geo-arch" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="zeit" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="anz_rei" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="prob_nr" constraints="0" unique_strength="0"/>
    <constraint notnull_strength="0" exp_strength="0" field="uuid" constraints="0" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="id"/>
    <constraint exp="&quot;messdatum&quot;" desc="" field="messdatum"/>
    <constraint exp="" desc="" field="aktcode"/>
    <constraint exp="" desc="" field="obj_type"/>
    <constraint exp="" desc="" field="obj_art"/>
    <constraint exp="" desc="" field="schnitt_nr"/>
    <constraint exp="" desc="" field="planum"/>
    <constraint exp="" desc="" field="material"/>
    <constraint exp="" desc="" field="bemerkung"/>
    <constraint exp="" desc="" field="bef_nr"/>
    <constraint exp="" desc="" field="fund_nr"/>
    <constraint exp="" desc="" field="geo-arch"/>
    <constraint exp="" desc="" field="zeit"/>
    <constraint exp="" desc="" field="anz_rei"/>
    <constraint exp="" desc="" field="prob_nr"/>
    <constraint exp="" desc="" field="uuid"/>
  </constraintExpressions>
  <expressionfields/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="aaaa" editable="0"/>
    <field name="aktcode" editable="1"/>
    <field name="anz_rei" editable="1"/>
    <field name="bef_nr" editable="1"/>
    <field name="bemerkung" editable="1"/>
    <field name="datierung" editable="1"/>
    <field name="fund_nr" editable="1"/>
    <field name="geo-arch" editable="1"/>
    <field name="geo_arch" editable="1"/>
    <field name="id" editable="1"/>
    <field name="material" editable="1"/>
    <field name="messdatum" editable="1"/>
    <field name="obj_art" editable="1"/>
    <field name="obj_type" editable="1"/>
    <field name="opj_art" editable="1"/>
    <field name="planum" editable="1"/>
    <field name="prob_nr" editable="1"/>
    <field name="schnitt_nr" editable="1"/>
    <field name="uuid" editable="1"/>
    <field name="zeit" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="aaaa" labelOnTop="0"/>
    <field name="aktcode" labelOnTop="0"/>
    <field name="anz_rei" labelOnTop="0"/>
    <field name="bef_nr" labelOnTop="0"/>
    <field name="bemerkung" labelOnTop="0"/>
    <field name="datierung" labelOnTop="0"/>
    <field name="fund_nr" labelOnTop="0"/>
    <field name="geo-arch" labelOnTop="0"/>
    <field name="geo_arch" labelOnTop="0"/>
    <field name="id" labelOnTop="0"/>
    <field name="material" labelOnTop="0"/>
    <field name="messdatum" labelOnTop="0"/>
    <field name="obj_art" labelOnTop="0"/>
    <field name="obj_type" labelOnTop="0"/>
    <field name="opj_art" labelOnTop="0"/>
    <field name="planum" labelOnTop="0"/>
    <field name="prob_nr" labelOnTop="0"/>
    <field name="schnitt_nr" labelOnTop="0"/>
    <field name="uuid" labelOnTop="0"/>
    <field name="zeit" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id</previewExpression>
  <layerGeometryType>2</layerGeometryType>
</qgis>
