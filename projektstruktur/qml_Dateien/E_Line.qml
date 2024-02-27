<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis readOnly="0" labelsEnabled="0" simplifyLocal="1" simplifyMaxScale="1" maxScale="0" simplifyAlgorithm="0" simplifyDrawingTol="1" styleCategories="LayerConfiguration|Symbology|Symbology3D|Labeling|Fields|Forms|Actions|MapTips|AttributeTable|Rendering|CustomProperties|GeometryOptions" hasScaleBasedVisibilityFlag="0" minScale="1e+08" simplifyDrawingHints="1" version="3.8.3-Zanzibar">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 forceraster="0" enableorderby="0" type="singleSymbol" symbollevels="0">
    <symbols>
      <symbol force_rhr="0" name="0" clip_to_extent="1" type="line" alpha="1">
        <layer enabled="1" locked="0" pass="0" class="SimpleLine">
          <prop v="round" k="capstyle"/>
          <prop v="0.66;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="round" k="joinstyle"/>
          <prop v="149,149,149,255" k="line_color"/>
          <prop v="dash" k="line_style"/>
          <prop v="0.3" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="ring_filter"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
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
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="id">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="messdatum">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option name="allow_null" type="bool" value="false"/>
            <Option name="calendar_popup" type="bool" value="true"/>
            <Option name="display_format" type="QString" value="yyyy-MM-dd"/>
            <Option name="field_format" type="QString" value="yyyy-MM-dd"/>
            <Option name="field_iso_format" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="aktcode">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="obj_type">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option name="AllowMulti" type="bool" value="false"/>
            <Option name="AllowNull" type="bool" value="true"/>
            <Option name="FilterExpression" type="QString" value="&quot;field_4&quot;  = '1' and  strpos(  &quot;field_5&quot; ,'Linie')>0"/>
            <Option name="Key" type="QString" value="field_1"/>
            <Option name="Layer" type="QString" value="Objekttypen_c35b1304_9467_40b5_a815_1c0e889d43c7"/>
            <Option name="LayerName" type="QString" value="Objekttypen"/>
            <Option name="LayerProviderName" type="QString" value="delimitedtext"/>
            <Option name="LayerSource" type="QString" value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt/Listen/Objekttypen.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes"/>
            <Option name="NofColumns" type="int" value="1"/>
            <Option name="OrderByValue" type="bool" value="true"/>
            <Option name="UseCompleter" type="bool" value="false"/>
            <Option name="Value" type="QString" value="field_1"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="obj_art">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option name="AllowMulti" type="bool" value="false"/>
            <Option name="AllowNull" type="bool" value="true"/>
            <Option name="FilterExpression" type="QString" value="strpos(  &quot;Field_2&quot; , concat( '|', current_value( 'obj_type' ),'|' ) ) > 0 and (&quot;Field_4&quot;  =  1)"/>
            <Option name="Key" type="QString" value="field_1"/>
            <Option name="Layer" type="QString" value="Objektarten_affd5a69_af7f_405b_a1d1_7847ba634da5"/>
            <Option name="LayerName" type="QString" value="Objektarten"/>
            <Option name="LayerProviderName" type="QString" value="delimitedtext"/>
            <Option name="LayerSource" type="QString" value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt/Listen/Objektarten.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes"/>
            <Option name="NofColumns" type="int" value="1"/>
            <Option name="OrderByValue" type="bool" value="true"/>
            <Option name="UseCompleter" type="bool" value="false"/>
            <Option name="Value" type="QString" value="field_1"/>
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
            <Option name="AllowMulti" type="bool" value="false"/>
            <Option name="AllowNull" type="bool" value="true"/>
            <Option name="FilterExpression" type="QString" value="strpos(  &quot;Field_2&quot; , concat( '|', current_value( 'obj_type' ),'|' ) ) > 0 and (&quot;Field_4&quot;  =  1)"/>
            <Option name="Key" type="QString" value="field_1"/>
            <Option name="Layer" type="QString" value="Material_daa89ee4_3d9a_4002_83bb_b99d305ceeb6"/>
            <Option name="LayerName" type="QString" value="Material"/>
            <Option name="LayerProviderName" type="QString" value="delimitedtext"/>
            <Option name="LayerSource" type="QString" value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt/Listen/Material.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes"/>
            <Option name="NofColumns" type="int" value="1"/>
            <Option name="OrderByValue" type="bool" value="true"/>
            <Option name="UseCompleter" type="bool" value="false"/>
            <Option name="Value" type="QString" value="field_1"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="benerkung">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="geo-arch">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option name="AllowMulti" type="bool" value="false"/>
            <Option name="AllowNull" type="bool" value="false"/>
            <Option name="FilterExpression" type="QString" value=""/>
            <Option name="Key" type="QString" value="field_1"/>
            <Option name="Layer" type="QString" value="geo_arch_d6d32e04_5d97_4afd_91a2_0df1add63c17"/>
            <Option name="LayerName" type="QString" value="geo_arch"/>
            <Option name="LayerProviderName" type="QString" value="delimitedtext"/>
            <Option name="LayerSource" type="QString" value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt/Listen/geo_arch.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes"/>
            <Option name="NofColumns" type="int" value="1"/>
            <Option name="OrderByValue" type="bool" value="true"/>
            <Option name="UseCompleter" type="bool" value="false"/>
            <Option name="Value" type="QString" value="field_1"/>
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
    <field name="prof_nr">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="zeit">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option name="AllowMulti" type="bool" value="false"/>
            <Option name="AllowNull" type="bool" value="true"/>
            <Option name="FilterExpression" type="QString" value=" &quot;field_7&quot;  = 1"/>
            <Option name="Key" type="QString" value="field_6"/>
            <Option name="Layer" type="QString" value="Zeiten_6f689fbf_7fa7_4148_8480_fbf74ef1b317"/>
            <Option name="LayerName" type="QString" value="Zeiten"/>
            <Option name="LayerProviderName" type="QString" value="delimitedtext"/>
            <Option name="LayerSource" type="QString" value="file:///D:/%23Projekt%20Tachy2GIS%23/WW-71_Projekt/Listen/Zeiten.csv?type=csv&amp;delimiter=;&amp;useHeader=No&amp;detectTypes=no&amp;geomType=none&amp;subsetIndex=no&amp;watchFile=yes"/>
            <Option name="NofColumns" type="int" value="1"/>
            <Option name="OrderByValue" type="bool" value="false"/>
            <Option name="UseCompleter" type="bool" value="false"/>
            <Option name="Value" type="QString" value="field_6"/>
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
    <field name="uuid">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" type="bool" value="false"/>
            <Option name="UseHtml" type="bool" value="false"/>
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
    <alias index="8" name="Bemerkung" field="benerkung"/>
    <alias index="9" name="Geo/Arch" field="geo-arch"/>
    <alias index="10" name="Befund-Nr" field="bef_nr"/>
    <alias index="11" name="Fund-Nr" field="fund_nr"/>
    <alias index="12" name="Profil-Nr" field="prof_nr"/>
    <alias index="13" name="" field="zeit"/>
    <alias index="14" name="" field="anz_rei"/>
    <alias index="15" name="" field="uuid"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression=" if (count( &quot;id&quot; )= 0 , 0, maximum( &quot;id&quot;)+1)" field="id" applyOnUpdate="0"/>
    <default expression=" now( )" field="messdatum" applyOnUpdate="0"/>
    <default expression=" @aktcode " field="aktcode" applyOnUpdate="0"/>
    <default expression=" if( @autoAttribute = 'True',  @obj_type ,'' ) " field="obj_type" applyOnUpdate="0"/>
    <default expression=" if( @autoAttribute = 'True',  @obj_art ,'' ) " field="obj_art" applyOnUpdate="0"/>
    <default expression=" if( @autoAttribute = 'True',  @schnitt_nr ,'' ) " field="schnitt_nr" applyOnUpdate="0"/>
    <default expression=" if( @autoAttribute = 'True',  @planum ,'' ) " field="planum" applyOnUpdate="0"/>
    <default expression=" if( @autoAttribute = 'True',  @material ,'' ) " field="material" applyOnUpdate="0"/>
    <default expression="" field="benerkung" applyOnUpdate="0"/>
    <default expression=" @arch-geo " field="geo-arch" applyOnUpdate="0"/>
    <default expression=" if( @autoAttribute = 'True',  @bef_nr ,'' ) " field="bef_nr" applyOnUpdate="0"/>
    <default expression=" if( @autoAttribute = 'True',  @fund_nr ,'' ) " field="fund_nr" applyOnUpdate="0"/>
    <default expression=" if( @autoAttribute = 'True',  @prof_nr ,'' ) " field="prof_nr" applyOnUpdate="0"/>
    <default expression="" field="zeit" applyOnUpdate="0"/>
    <default expression="" field="anz_rei" applyOnUpdate="0"/>
    <default expression="uuid()" field="uuid" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint unique_strength="0" notnull_strength="0" field="id" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="messdatum" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="aktcode" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="obj_type" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="obj_art" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="schnitt_nr" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="planum" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="material" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="benerkung" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="geo-arch" constraints="4" exp_strength="2"/>
    <constraint unique_strength="0" notnull_strength="0" field="bef_nr" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="fund_nr" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="prof_nr" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="zeit" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="anz_rei" constraints="0" exp_strength="0"/>
    <constraint unique_strength="0" notnull_strength="0" field="uuid" constraints="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" field="id" desc=""/>
    <constraint exp="" field="messdatum" desc=""/>
    <constraint exp="" field="aktcode" desc=""/>
    <constraint exp="" field="obj_type" desc=""/>
    <constraint exp="" field="obj_art" desc=""/>
    <constraint exp="" field="schnitt_nr" desc=""/>
    <constraint exp="" field="planum" desc=""/>
    <constraint exp="" field="material" desc=""/>
    <constraint exp="" field="benerkung" desc=""/>
    <constraint exp="&quot;id&quot;" field="geo-arch" desc=""/>
    <constraint exp="" field="bef_nr" desc=""/>
    <constraint exp="" field="fund_nr" desc=""/>
    <constraint exp="" field="prof_nr" desc=""/>
    <constraint exp="" field="zeit" desc=""/>
    <constraint exp="" field="anz_rei" desc=""/>
    <constraint exp="" field="uuid" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortExpression="&quot;benerkung&quot;" actionWidgetStyle="dropDown" sortOrder="0">
    <columns>
      <column name="id" type="field" hidden="0" width="78"/>
      <column name="messdatum" type="field" hidden="0" width="126"/>
      <column name="aktcode" type="field" hidden="0" width="83"/>
      <column name="obj_type" type="field" hidden="0" width="125"/>
      <column name="obj_art" type="field" hidden="0" width="160"/>
      <column name="schnitt_nr" type="field" hidden="0" width="100"/>
      <column name="planum" type="field" hidden="0" width="67"/>
      <column name="bef_nr" type="field" hidden="0" width="186"/>
      <column name="fund_nr" type="field" hidden="0" width="83"/>
      <column name="prof_nr" type="field" hidden="0" width="75"/>
      <column name="benerkung" type="field" hidden="0" width="188"/>
      <column name="material" type="field" hidden="0" width="79"/>
      <column name="zeit" type="field" hidden="0" width="74"/>
      <column name="geo-arch" type="field" hidden="0" width="52"/>
      <column name="anz_rei" type="field" hidden="0" width="84"/>
      <column type="actions" hidden="1" width="-1"/>
      <column name="uuid" type="field" hidden="0" width="-1"/>
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
    <field name="benerkung" editable="1"/>
    <field name="fund_nr" editable="1"/>
    <field name="geo-arch" editable="1"/>
    <field name="gok" editable="1"/>
    <field name="id" editable="1"/>
    <field name="material" editable="1"/>
    <field name="messdatum" editable="1"/>
    <field name="obj_art" editable="1"/>
    <field name="obj_type" editable="1"/>
    <field name="planum" editable="1"/>
    <field name="prof_nr" editable="1"/>
    <field name="schnitt_nr" editable="1"/>
    <field name="uuid" editable="1"/>
    <field name="zeit" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="aaa" labelOnTop="0"/>
    <field name="aktcode" labelOnTop="0"/>
    <field name="anz_rei" labelOnTop="0"/>
    <field name="bef_nr" labelOnTop="0"/>
    <field name="benerkung" labelOnTop="0"/>
    <field name="fund_nr" labelOnTop="0"/>
    <field name="geo-arch" labelOnTop="0"/>
    <field name="gok" labelOnTop="0"/>
    <field name="id" labelOnTop="0"/>
    <field name="material" labelOnTop="0"/>
    <field name="messdatum" labelOnTop="0"/>
    <field name="obj_art" labelOnTop="0"/>
    <field name="obj_type" labelOnTop="0"/>
    <field name="planum" labelOnTop="0"/>
    <field name="prof_nr" labelOnTop="0"/>
    <field name="schnitt_nr" labelOnTop="0"/>
    <field name="uuid" labelOnTop="0"/>
    <field name="zeit" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id</previewExpression>
  <mapTip>&lt;b > &lt;font color="blue">&lt;font size="4"> Objekttyp:  &lt;/b>&lt;font color="black">[% "obj_type" %] &lt;br>&#xd;
&lt;b > &lt;font color="blue"> Objektart:  &lt;/b>&lt;font color="black">[% "obj_art" %]&lt;br>&#xd;
</mapTip>
  <layerGeometryType>1</layerGeometryType>
</qgis>
