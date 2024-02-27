<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyMaxScale="1" minScale="1e+08" labelsEnabled="0" simplifyLocal="1" readOnly="0" styleCategories="LayerConfiguration|Symbology|Symbology3D|Labeling|Fields|Forms|Actions|MapTips|AttributeTable|Rendering|CustomProperties|GeometryOptions" version="3.4.1-Madeira" hasScaleBasedVisibilityFlag="0" simplifyDrawingTol="1" maxScale="0" simplifyDrawingHints="0" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 enableorderby="0" forceraster="0" type="singleSymbol" symbollevels="0">
    <symbols>
      <symbol alpha="1" name="0" type="marker" clip_to_extent="1">
        <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
          <prop k="angle" v="0"/>
          <prop k="color" v="121,121,121,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="195,195,195,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="1.5"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property value="id" key="dualview/previewExpressions"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
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
            <Option name="allow_null" value="false" type="bool"/>
            <Option name="calendar_popup" value="true" type="bool"/>
            <Option name="display_format" value="yyyy-MM-dd" type="QString"/>
            <Option name="field_format" value="yyyy-MM-dd" type="QString"/>
            <Option name="field_iso_format" value="false" type="bool"/>
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
            <Option name="AllowMulti" value="false" type="bool"/>
            <Option name="AllowNull" value="true" type="bool"/>
            <Option name="FilterExpression" value="&quot;field_4&quot;  = '1' and  strpos(  &quot;field_5&quot; ,'Linie')>0" type="QString"/>
            <Option name="Key" value="field_1" type="QString"/>
            <Option name="Layer" value="Objekttypen_c35b1304_9467_40b5_a815_1c0e889d43c7" type="QString"/>
            <Option name="NofColumns" value="1" type="int"/>
            <Option name="OrderByValue" value="true" type="bool"/>
            <Option name="UseCompleter" value="false" type="bool"/>
            <Option name="Value" value="field_1" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="obj_art">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option name="AllowMulti" value="false" type="bool"/>
            <Option name="AllowNull" value="true" type="bool"/>
            <Option name="FilterExpression" value="strpos(  &quot;Field_2&quot; , concat( '|', current_value( 'obj_type' ),'|' ) ) > 0 and (&quot;Field_4&quot;  =  1)" type="QString"/>
            <Option name="Key" value="field_1" type="QString"/>
            <Option name="Layer" value="Objektarten_affd5a69_af7f_405b_a1d1_7847ba634da5" type="QString"/>
            <Option name="NofColumns" value="1" type="int"/>
            <Option name="OrderByValue" value="true" type="bool"/>
            <Option name="UseCompleter" value="false" type="bool"/>
            <Option name="Value" value="field_1" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="schnitt_nr">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
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
            <Option name="AllowMulti" value="false" type="bool"/>
            <Option name="AllowNull" value="false" type="bool"/>
            <Option name="FilterExpression" value="strpos(  &quot;Field_2&quot; , concat( '|', current_value( 'obj_type' ),'|' ) ) > 0 and (&quot;Field_4&quot;  =  1)" type="QString"/>
            <Option name="Key" value="field_1" type="QString"/>
            <Option name="Layer" value="Material_daa89ee4_3d9a_4002_83bb_b99d305ceeb6" type="QString"/>
            <Option name="NofColumns" value="1" type="int"/>
            <Option name="OrderByValue" value="true" type="bool"/>
            <Option name="UseCompleter" value="false" type="bool"/>
            <Option name="Value" value="field_1" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung">
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
            <Option name="AllowMulti" value="false" type="bool"/>
            <Option name="AllowNull" value="false" type="bool"/>
            <Option name="FilterExpression" value="" type="QString"/>
            <Option name="Key" value="field_1" type="QString"/>
            <Option name="Layer" value="geo_arch_d6d32e04_5d97_4afd_91a2_0df1add63c17" type="QString"/>
            <Option name="NofColumns" value="1" type="int"/>
            <Option name="OrderByValue" value="true" type="bool"/>
            <Option name="UseCompleter" value="false" type="bool"/>
            <Option name="Value" value="field_1" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bef_nr">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="ptnr">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
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
    <field name="prob_nr">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="zeit">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option name="AllowMulti" value="false" type="bool"/>
            <Option name="AllowNull" value="true" type="bool"/>
            <Option name="FilterExpression" value=" &quot;field_7&quot;  = 1" type="QString"/>
            <Option name="Key" value="field_6" type="QString"/>
            <Option name="Layer" value="Zeiten_6f689fbf_7fa7_4148_8480_fbf74ef1b317" type="QString"/>
            <Option name="LayerName" value="Zeiten" type="QString"/>
            <Option name="LayerProviderName" value="delimitedtext" type="QString"/>
            <Option name="LayerSource" value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt/Listen/Zeiten.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes" type="QString"/>
            <Option name="NofColumns" value="1" type="int"/>
            <Option name="OrderByValue" value="false" type="bool"/>
            <Option name="UseCompleter" value="false" type="bool"/>
            <Option name="Value" value="field_6" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="anz_rei">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="prof_nr">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="uuid">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias name="" field="id" index="0"/>
    <alias name="Aufnamedatum" field="messdatum" index="1"/>
    <alias name="Grabung" field="aktcode" index="2"/>
    <alias name="Objekttyp" field="obj_type" index="3"/>
    <alias name="Objektart" field="obj_art" index="4"/>
    <alias name="Schnitt-Nr" field="schnitt_nr" index="5"/>
    <alias name="Planum" field="planum" index="6"/>
    <alias name="Material" field="material" index="7"/>
    <alias name="Bemerkung" field="bemerkung" index="8"/>
    <alias name="Geo/Arch" field="geo-arch" index="9"/>
    <alias name="Befund-Nr" field="bef_nr" index="10"/>
    <alias name="" field="ptnr" index="11"/>
    <alias name="Fund-Nr" field="fund_nr" index="12"/>
    <alias name="Probe-Nr" field="prob_nr" index="13"/>
    <alias name="" field="zeit" index="14"/>
    <alias name="" field="anz_rei" index="15"/>
    <alias name="Profil-Nr" field="prof_nr" index="16"/>
    <alias name="" field="uuid" index="17"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression=" if (count( &quot;id&quot; )= 0 , 0, maximum( &quot;id&quot;)+1)" applyOnUpdate="0" field="id"/>
    <default expression="now()" applyOnUpdate="0" field="messdatum"/>
    <default expression=" @aktcode " applyOnUpdate="0" field="aktcode"/>
    <default expression=" if( @autoAttribute = 'True',  @obj_type ,'' ) " applyOnUpdate="0" field="obj_type"/>
    <default expression=" if( @autoAttribute = 'True',  @obj_art ,'' ) " applyOnUpdate="0" field="obj_art"/>
    <default expression=" if( @autoAttribute = 'True',  @schnitt_nr ,'' ) " applyOnUpdate="0" field="schnitt_nr"/>
    <default expression=" if( @autoAttribute = 'True',  @planum ,'' ) " applyOnUpdate="0" field="planum"/>
    <default expression=" if( @autoAttribute = 'True',  @material ,'' ) " applyOnUpdate="0" field="material"/>
    <default expression="" applyOnUpdate="0" field="bemerkung"/>
    <default expression=" @arch-geo " applyOnUpdate="0" field="geo-arch"/>
    <default expression=" if( @autoAttribute = 'True',  @bef_nr ,'' ) " applyOnUpdate="0" field="bef_nr"/>
    <default expression=" if( @autoAttribute = 'True',  @ptnr ,'' ) " applyOnUpdate="0" field="ptnr"/>
    <default expression=" if( @autoAttribute = 'True',  @fund_nr ,'' ) " applyOnUpdate="0" field="fund_nr"/>
    <default expression=" if( @autoAttribute = 'True',  @prob_nr ,'' ) " applyOnUpdate="0" field="prob_nr"/>
    <default expression="" applyOnUpdate="0" field="zeit"/>
    <default expression="" applyOnUpdate="0" field="anz_rei"/>
    <default expression="" applyOnUpdate="0" field="prof_nr"/>
    <default expression="uuid()" applyOnUpdate="0" field="uuid"/>
  </defaults>
  <constraints>
    <constraint notnull_strength="0" constraints="0" field="id" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="4" field="messdatum" unique_strength="0" exp_strength="2"/>
    <constraint notnull_strength="0" constraints="0" field="aktcode" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="obj_type" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="obj_art" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="schnitt_nr" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="planum" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="material" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="bemerkung" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="geo-arch" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="bef_nr" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="ptnr" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="fund_nr" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="prob_nr" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="zeit" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="anz_rei" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="prof_nr" unique_strength="0" exp_strength="0"/>
    <constraint notnull_strength="0" constraints="0" field="uuid" unique_strength="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="id" exp="" desc=""/>
    <constraint field="messdatum" exp=" now( )" desc=""/>
    <constraint field="aktcode" exp="" desc=""/>
    <constraint field="obj_type" exp="" desc=""/>
    <constraint field="obj_art" exp="" desc=""/>
    <constraint field="schnitt_nr" exp="" desc=""/>
    <constraint field="planum" exp="" desc=""/>
    <constraint field="material" exp="" desc=""/>
    <constraint field="bemerkung" exp="" desc=""/>
    <constraint field="geo-arch" exp="" desc=""/>
    <constraint field="bef_nr" exp="" desc=""/>
    <constraint field="ptnr" exp="" desc=""/>
    <constraint field="fund_nr" exp="" desc=""/>
    <constraint field="prob_nr" exp="" desc=""/>
    <constraint field="zeit" exp="" desc=""/>
    <constraint field="anz_rei" exp="" desc=""/>
    <constraint field="prof_nr" exp="" desc=""/>
    <constraint field="uuid" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="&quot;bef_nr&quot;" actionWidgetStyle="dropDown">
    <columns>
      <column width="52" name="id" hidden="0" type="field"/>
      <column width="118" name="messdatum" hidden="0" type="field"/>
      <column width="95" name="aktcode" hidden="0" type="field"/>
      <column width="180" name="obj_type" hidden="0" type="field"/>
      <column width="125" name="obj_art" hidden="0" type="field"/>
      <column width="117" name="schnitt_nr" hidden="0" type="field"/>
      <column width="80" name="planum" hidden="0" type="field"/>
      <column width="70" name="bef_nr" hidden="0" type="field"/>
      <column width="109" name="ptnr" hidden="0" type="field"/>
      <column width="94" name="prof_nr" hidden="0" type="field"/>
      <column width="94" name="fund_nr" hidden="0" type="field"/>
      <column width="104" name="prob_nr" hidden="0" type="field"/>
      <column width="76" name="material" hidden="0" type="field"/>
      <column width="197" name="bemerkung" hidden="0" type="field"/>
      <column width="71" name="zeit" hidden="0" type="field"/>
      <column width="52" name="geo-arch" hidden="0" type="field"/>
      <column width="85" name="anz_rei" hidden="0" type="field"/>
      <column width="-1" hidden="1" type="actions"/>
      <column width="-1" name="uuid" hidden="0" type="field"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
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
    <field name="aaa" editable="0"/>
    <field name="aktcode" editable="1"/>
    <field name="anz_rei" editable="1"/>
    <field name="bef_nr" editable="1"/>
    <field name="bemerkung" editable="1"/>
    <field name="fund_nr" editable="1"/>
    <field name="geo-arch" editable="1"/>
    <field name="id" editable="1"/>
    <field name="material" editable="1"/>
    <field name="messdatum" editable="1"/>
    <field name="obj_art" editable="1"/>
    <field name="obj_type" editable="1"/>
    <field name="planum" editable="1"/>
    <field name="prob_nr" editable="1"/>
    <field name="prof_nr" editable="1"/>
    <field name="ptnr" editable="1"/>
    <field name="schnitt_nr" editable="1"/>
    <field name="uuid" editable="1"/>
    <field name="zeit" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="aaa" labelOnTop="0"/>
    <field name="aktcode" labelOnTop="0"/>
    <field name="anz_rei" labelOnTop="0"/>
    <field name="bef_nr" labelOnTop="0"/>
    <field name="bemerkung" labelOnTop="0"/>
    <field name="fund_nr" labelOnTop="0"/>
    <field name="geo-arch" labelOnTop="0"/>
    <field name="id" labelOnTop="0"/>
    <field name="material" labelOnTop="0"/>
    <field name="messdatum" labelOnTop="0"/>
    <field name="obj_art" labelOnTop="0"/>
    <field name="obj_type" labelOnTop="0"/>
    <field name="planum" labelOnTop="0"/>
    <field name="prob_nr" labelOnTop="0"/>
    <field name="prof_nr" labelOnTop="0"/>
    <field name="ptnr" labelOnTop="0"/>
    <field name="schnitt_nr" labelOnTop="0"/>
    <field name="uuid" labelOnTop="0"/>
    <field name="zeit" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id</previewExpression>
  <mapTip>&lt;b > &lt;font color="blue">&lt;font size="4"> Objekttyp:  &lt;/b>&lt;font color="black">[% "obj_type" %] &lt;br>&#xd;
&lt;b > &lt;font color="blue"> Objektart:  &lt;/b>&lt;font color="black">[% "obj_art" %]&lt;br></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
