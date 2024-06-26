<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:ukl="https://www.legislation.gov.uk/namespaces/UK-AKN"
    xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
    exclude-result-prefixes="xs"
    version="2.0">

    <xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" version="5"/>

    <!-- Input parameter specified when transformation is run -->
    <!-- this is for a path (uri) to the folder where the XML from Lawmaker is saved -->
    <!-- for marshaling -->
    <xsl:param name="marsh-path"/>

    <!-- we need stable=yes to make the document-uri function work -->
    <xsl:variable name="todays-papers" select="collection(concat($marsh-path, '?select=*.xml;stable=yes'))"/>
    <!-- FramMaker of the above: <xsl:variable name="todays-papers" select="collection(concat($marsh-path, '?select=*.xml'))/Amendments.Commons"/> -->


    <!-- MNIS data for name checks -->
    <xsl:variable name="mnis-name" select="document('http://data.parliament.uk/membersdataplatform/services/mnis/members/query/House=Commons%7CIsEligible=true/')/Members"/>


    <xsl:template match="root">

        <xsl:message>$marsh-path: <xsl:value-of select="$marsh-path"/></xsl:message>

        <html>
            <head>
                <title><!--<xsl:value-of select="concat(current-date(), ' Added Names')"/>-->Added Names Report</title>
                <style>html {font-family:"Segoe UI", Frutiger, "Frutiger Linotype", "Dejavu Sans", "Helvetica Neue", Arial, sans-serif;background-color:#ebe9e8;word-wrap:normal;white-space:normal;} body {width:70%;background-color:#ffffff;margin-left:30px;margin:auto;overflow-wrap: break-word;padding-bottom:20px;} .header {background-color:#373151;color:#ffffff;} .number-summary-count {padding-left:20px;margin-bottom:20px} .amendment {margin-bottom:20px;margin-left:20px;border:2px solid #ebe9e8;padding-left:10px;width:80%;min-width:200px;padding-bottom:10px} .bill-title {color:black;background-color:#ffffff;padding-left:20px;} hr {color:#006e46;} .main-heading {padding-left:20px;padding-top:20px;}.main-summary {padding:0 0 10px 20px} .num-info {border-bottom: 1px dotted #ebe9e8;} .bill-reminder {text-align:right;color:#4d4d4d;font-size:10px;padding-right:5px;} .check-box {text-align:right;padding-top:10px;padding-right:20px;border-top:1px dotted #ebe9e8;} .red {color:red} .green {color: green}</style>
            </head>
            <body>
                <!-- Header section with main heading and selection of bills -->
                <div class="header">
                    <div class="main-heading">
                        <h1>Added Names report <br></br><xsl:value-of select="downloaded"/></h1>
                    </div>
                    <div class="main-summary">
                        <xsl:choose>
                            <xsl:when test="count(distinct-values(item/bill)) > 1">
                                <p><xsl:value-of select="concat(count(distinct-values(item/bill)), ' papers have added names today:')"/></p>
                            </xsl:when>
                            <xsl:otherwise>
                                <p><xsl:text>Only one paper has added names today:</xsl:text></p>
                            </xsl:otherwise>
                        </xsl:choose>

                        <ul>
                            <xsl:for-each-group select="item" group-by="bill">
                                <li><a href="{concat('#',lower-case(replace(current-grouping-key(), ' ', '-')))}" style="color:white"><xsl:value-of select="current-grouping-key()"/></a></li>
                            </xsl:for-each-group>
                        </ul>
                        <xsl:choose>
                            <xsl:when test="$todays-papers">
                                <p>If you provide LawMaker XML: <span class="green"> &#x2714;</span> indicates that names have been added already, <span class="red"> &#x2718;</span> indicates that the name has not yet been added (at least not in the XML provided). You can turn these indicators on or off: <button id="name-in-xml-indicator-toggle-btn">Turn off</button> </p>
                                <p>The following XML files have been used for marshalling: <button id="show-hide-marshalling-xml-files-btn">Show files</button></p>
                                <div id="collapsible-xml-files" style="display: none;">
                                    <ul>
                                        <xsl:for-each select="$todays-papers" >
                                            <li><xsl:value-of select="tokenize(document-uri(.), '/')[last()]"/></li>
                                        </xsl:for-each>
                                    </ul>
                                </div>
                            </xsl:when>
                            <xsl:otherwise>
                                <p>No marshalling XML found</p>
                            </xsl:otherwise>
                        </xsl:choose>
                    </div>
                </div>
                <xsl:call-template name="reportBody">
                    <xsl:with-param name="todays-papers" select="$todays-papers"></xsl:with-param>
                </xsl:call-template>
                <script>
                  document.addEventListener("DOMContentLoaded", function() {

                    const toggleNameIndicatorsBtn = document.querySelector("#name-in-xml-indicator-toggle-btn");
                    const toggleMarshallingXmlFilesBtn = document.querySelector("#show-hide-marshalling-xml-files-btn");
                    const nameIndicators = document.querySelectorAll(".name-in-xml-indicator");
                    const collapsibleXmlFilesSection = document.querySelector("#collapsible-xml-files");

                    toggleNameIndicatorsBtn.addEventListener("click", function(){

                      if (toggleNameIndicatorsBtn.innerHTML === "Turn off") {
                        toggleNameIndicatorsBtn.innerHTML = "Turn on";
                      } else {
                        toggleNameIndicatorsBtn.innerHTML = "Turn off";
                      }

                      nameIndicators.forEach(function(nameIndicators) {
                        if (nameIndicators.style.display === "none") {
                          nameIndicators.style.display = "inline";
                        } else {
                          nameIndicators.style.display = "none";
                        }
                      });
                    });

                    toggleMarshallingXmlFilesBtn.addEventListener("click", function(){
                      if (toggleMarshallingXmlFilesBtn.innerHTML === "Show files") {
                        toggleMarshallingXmlFilesBtn.innerHTML = "Hide files";
                      } else {
                        toggleMarshallingXmlFilesBtn.innerHTML = "Show files";
                      }
                      if (collapsibleXmlFilesSection.style.display === "none") {
                        collapsibleXmlFilesSection.style.display = "block";
                      } else {
                        collapsibleXmlFilesSection.style.display = "none";
                      }
                    });
                  });
                </script>
            </body>
        </html>
    </xsl:template>

    <xsl:template name="reportBody" >
        <xsl:param name="todays-papers" required="yes"/>

        <xsl:for-each-group select="item[omit-from-report/text()!='true']" group-by="bill">
            <!-- where omit from report is true nothing should be output. These are Micks instructions -->
            <xsl:variable name="bill-grouping-key" select="current-grouping-key()"/>
            <xsl:variable name="current-group-var" select="current-group()"/>
            <!--## BILL ##-->
            <div class="bill" id="{lower-case(replace(current-grouping-key(), ' ', '-'))}">

                <!-- Add bill title as heading -->
                <h1 class="bill-title"><xsl:value-of select="current-grouping-key()"/></h1>

                <!-- Summary of amendment numbers affected -->
                <div class="number-summary">
                    <div class="number-summary-count"><p>Amendments in this paper with names added/removed: <b><xsl:value-of select="count(distinct-values(current-group()/descendant::matched-numbers/amd-no))"/></b></p></div>
                </div>

                <!--## AMDT NO ##-->
                <!-- Amendments that can be displayed in marshalled order -->
                <!-- For each amendment number in the matching Lawmaker XML file... -->
                <xsl:for-each select="$todays-papers[normalize-space(descendant::akn:TLCConcept[@eId='varBillTitle']/@showAs) = $bill-grouping-key]/descendant::akn:num[@ukl:dnum] | $todays-papers/Amendments.Commons[normalize-space(replace(descendant::STText, ', As Amended', '')) = $bill-grouping-key]/descendant::*[local-name()='Amendment.Number']">
                    <!--FrameMaker only version of above: <xsl:for-each select="$todays-papers[normalize-space(descendant::STText) = $bill-grouping-key]/descendant::*[local-name()='Amendment.Number']"> -->

                    <!--<xsl:message><xsl:value-of select="name(.)"/></xsl:message>-->
                    <xsl:variable name="is_lawmaker" select="boolean(ancestor::akn:akomaNtoso)"/>

                    <xsl:variable name="current-amdt" select="."/>
                    <xsl:variable name="current-lm-supporter-blocks" select="$current-amdt/ancestor::akn:amendmentBody/akn:amendmentHeading/akn:block[@name='proposer' or @name='supporters']"/>

                    <!-- ...group all the added names items that match the amendment number and put them in div[@class='amendment'] -->
                    <xsl:for-each-group select="$current-group-var/descendant::matched-numbers" group-by="amd-no[.=upper-case($current-amdt)]">

                        <div class="amendment">

                            <div class="bill-reminder">
                                <xsl:value-of select="$bill-grouping-key"/>
                            </div>

                            <div class="num-info">
                                <h2 class="amendment-number">
                                    <xsl:choose>
                                        <!-- Add "Amendment" prefix to amendment numbers -->
                                        <xsl:when test="not(matches(current-grouping-key(), '(NC|NS)'))">
                                            <xsl:value-of select="concat('Amendment ', current-grouping-key())"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:value-of select="current-grouping-key()"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </h2>
                            </div>

                            <!--## NAMES TO ADD ##-->
                            <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::names-to-add/matched-names/name | current-group()/ancestor::item/further-names-to-add/matched-names/furtherName) > 0">
                                <div class="names-to-add">
                                    <h4>Names to add</h4>
                                    <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::names-to-add/descendant::name | current-group()/ancestor::item/further-names-to-add/matched-names/furtherName">
                                        <xsl:variable name="current-name" select="."/>
                                        <div class="name">
                                            <span>
                                                <!-- Link each name back to item on Added Names page -->
                                                <a title="{concat('Dashboard ID:', ancestor::names-to-add/preceding-sibling::dashboard-id)}" href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', ancestor::names-to-add/preceding-sibling::dashboard-id)}">
                                                    <xsl:choose>
                                                        <!-- If name does not match MNIS, add highlight -->
                                                        <xsl:when test="not(. = $mnis-name/Member/DisplayAs)">
                                                            <xsl:attribute name="style">
                                                                <xsl:text>text-decoration: underline red 1px; color: black;</xsl:text>
                                                            </xsl:attribute>
                                                        </xsl:when>
                                                        <!-- Otherwise, text will be black with no decoration -->
                                                        <xsl:otherwise>
                                                            <xsl:attribute name="style">
                                                                <xsl:text>text-decoration: none; color: black;</xsl:text>
                                                            </xsl:attribute>
                                                        </xsl:otherwise>
                                                    </xsl:choose>
                                                    <xsl:value-of select="$current-name"/>
                                                </a>

                                                <xsl:if test="$is_lawmaker">
                                                    <!-- Add tick if name is found or cross if it is not. This will only work with lawmaker files. -->
                                                    <xsl:choose>
                                                        <xsl:when test="$current-lm-supporter-blocks/*[@refersTo][normalize-space(text()) = $current-name/normalize-space(text())]">
                                                            <!-- The current name has been found in the supporters list -->
                                                            <span class="green name-in-xml-indicator"  title="This name appears to have been added."> &#x2714;</span>
                                                        </xsl:when>
                                                        <xsl:otherwise>
                                                            <span class="red name-in-xml-indicator"  title="This name does not appear to have been added."> &#x2718;</span>
                                                        </xsl:otherwise>
                                                    </xsl:choose>
                                                </xsl:if>
                                            </span>
                                        </div>
                                    </xsl:for-each>
                                </div>
                            </xsl:if>


                            <!--### NAMES TO REMOVE ###-->
                            <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::names-to-remove/matched-names/name) > 0">
                                <div class="names-to-remove">
                                    <h4>Names to remove</h4>
                                    <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::names-to-remove/descendant::name">
                                        <div class="name">
                                            <span>
                                                <a title="{concat('Dashboard ID:', ancestor::names-to-remove/preceding-sibling::dashboard-id)}" href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', ancestor::names-to-remove/preceding-sibling::dashboard-id)}"><xsl:value-of select="."/></a></span>
                                        </div>
                                    </xsl:for-each>

                                </div>
                            </xsl:if>

                            <!--### COMMENTS ###-->
                            <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::comments/p) > 0">
                                <div class="comments">
                                    <h4 style="margin-bottom:5px;margin-top:30px;">Comments</h4>
                                    <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::comments">
                                        <p style="font-size:smaller;color:#4d4d4d;"><a href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', @dashboard-id)}" style="text-decoration:none;color;color:#4d4d4d;"><b>Dashboard ID: <xsl:value-of select="@dashboard-id"/></b></a></p>
                                        <xsl:for-each select="p">
                                            <p title="{concat('Dashboard ID:', parent::comments/@dashboard-id)}" style="font-size:smaller;color:#4d4d4d;line-height:90%;">
                                                <i><xsl:value-of select="."/></i>
                                            </p>
                                        </xsl:for-each>
                                    </xsl:for-each>
                                </div>
                            </xsl:if>
                            <div class="check-box">
                                <input type="checkbox"/>
                                <label>Checked</label>
                            </div>

                        </div><!-- End of amendment div -->
                    </xsl:for-each-group>

                </xsl:for-each><!-- End marshalled order amendments -->


                <!-- Amendments that could not be matched/put in marshalled order -->
                <xsl:for-each-group select="$current-group-var/descendant::matched-numbers" group-by="amd-no">
                    <xsl:choose>
                        <!-- ignore amendments that have already been marshalled from *LawMaker* -->
                        <xsl:when test="current-grouping-key() = $todays-papers[normalize-space(descendant::akn:TLCConcept[@eId='varBillTitle']/@showAs) = $bill-grouping-key]/descendant::akn:num[@ukl:dnum]"></xsl:when>

                        <!-- ignore amendments that have already been marshalled from *FrameMaker*  -->
                        <xsl:when test="current-grouping-key() = $todays-papers/Amendments.Commons[normalize-space(replace(descendant::STText, ', As Amended', '')) = $bill-grouping-key]/descendant::*[local-name()='Amendment.Number']"></xsl:when>

                        <xsl:otherwise>
                            <div class="amendment">
                                <div class="bill-reminder">
                                    <xsl:value-of select="$bill-grouping-key"/>
                                </div>

                                <div class="num-info">
                                    <h2 class="amendment-number">
                                        <xsl:choose>
                                            <!-- Add "Amendment" prefix to amendment numbers -->
                                            <xsl:when test="not(matches(current-grouping-key(), '(NC|NS)'))">
                                                <xsl:value-of select="concat('Amendment ', current-grouping-key())"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:value-of select="current-grouping-key()"/>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                        <span style="font-family:Segoe UI Symbol;color:red;font-weight:normal;padding-left:10px" title="This amendment is not shown in marshalled order. It may be that the amendment has been withdrawn, it is newly tabled or no XML was supplied to determine marshalled order">&#9888;</span>
                                    </h2>
                                </div>

                                <!--## NAMES TO ADD ##-->
                                <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::names-to-add/matched-names/name | current-group()/ancestor::item/further-names-to-add/matched-names/furtherName)  > 0">
                                    <div class="names-to-add">
                                        <h4>Names to add</h4>
                                        <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::names-to-add/descendant::name | current-group()/ancestor::item/further-names-to-add/matched-names/furtherName">
                                            <div class="name">
                                                <span>
                                                    <!-- Link each name back to item on Added Names page -->
                                                    <a title="{concat('Dashboard ID:', ancestor::names-to-add/preceding-sibling::dashboard-id)}" href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', ancestor::names-to-add/preceding-sibling::dashboard-id)}">
                                                        <xsl:choose>
                                                            <!-- If name does not match MNIS, add highlight -->
                                                            <xsl:when test="not(. = $mnis-name/Member/DisplayAs)">
                                                                <xsl:attribute name="style">
                                                                    <xsl:text>text-decoration: underline red 1px; color: black;</xsl:text>
                                                                </xsl:attribute>
                                                            </xsl:when>
                                                            <!-- Otherwise, text will be black with no decoration -->
                                                            <xsl:otherwise>
                                                                <xsl:attribute name="style">
                                                                    <xsl:text>text-decoration: none; color: black;</xsl:text>
                                                                </xsl:attribute>
                                                            </xsl:otherwise>
                                                        </xsl:choose>
                                                        <xsl:value-of select="."/>
                                                    </a>
                                                </span>
                                            </div>
                                        </xsl:for-each>
                                    </div>
                                </xsl:if>


                                <!--### NAMES TO REMOVE ###-->
                                <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::names-to-remove/matched-names/name) > 0">
                                    <div class="names-to-remove">
                                        <h4>Names to remove</h4>
                                        <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::names-to-remove/descendant::name">
                                            <div class="name">
                                                <span>
                                                    <a title="{concat('Dashboard ID:', ancestor::names-to-remove/preceding-sibling::dashboard-id)}" href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', ancestor::names-to-remove/preceding-sibling::dashboard-id)}"><xsl:value-of select="."/></a></span>
                                            </div>
                                        </xsl:for-each>

                                    </div>
                                </xsl:if>

                                <!--### COMMENTS ###-->
                                <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::comments/p) > 0">
                                    <div class="comments">
                                        <h4 style="margin-bottom:5px;margin-top:30px;">Comments</h4>
                                        <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::comments">
                                            <p style="font-size:smaller;color:#4d4d4d;"><a href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', @dashboard-id)}" style="text-decoration:none;color;color:#4d4d4d;"><b>Dashboard ID: <xsl:value-of select="@dashboard-id"/></b></a></p>
                                            <xsl:for-each select="p">
                                                <p title="{concat('Dashboard ID:', parent::comments/@dashboard-id)}" style="font-size:smaller;color:#4d4d4d;line-height:80%;">
                                                    <i><xsl:value-of select="."/></i>
                                                </p>
                                            </xsl:for-each>
                                        </xsl:for-each>
                                    </div>
                                </xsl:if>
                                <!-- Check box as aide memoire for those checking the paper -->
                                <div class="check-box">
                                    <input type="checkbox"/>
                                    <label>Checked</label>
                                </div>
                            </div>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each-group>

            </div>
        </xsl:for-each-group>

    </xsl:template>
</xsl:stylesheet>
