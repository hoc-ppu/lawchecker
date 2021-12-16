<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    version="2.0">
    
    <xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" version="5"/>
    
    <!-- variable below not yet in use, intended for getting info from standing amendment content (e.g. marshalling order, standing names) -->
    <xsl:variable name="todays-papers" select="collection('../XML/FrameMakerXML?select=*.xml')/Amendments.Commons"/>
    
    
    
    <!-- MNIS data for name checks -->
    <xsl:variable name="mnis-name" select="document('http://data.parliament.uk/membersdataplatform/services/mnis/members/query/House=Commons%7CIsEligible=true/')/Members"/>
    
    
    <xsl:template match="root">
        <html>
            <head>
                <title><xsl:value-of select="concat(current-date(), ' Added Names')"/></title>
                <style>html {font-family:"Segoe UI", Frutiger, "Frutiger Linotype", "Dejavu Sans", "Helvetica Neue", Arial, sans-serif;background-color:#ebe9e8;word-wrap:normal;white-space:normal;} body {width:70%;background-color:#ffffff;margin-left:30px;margin:auto;overflow-wrap: break-word;padding-bottom:20px;} .header {background-color:#373151;color:#ffffff;} .number-summary-count {margin-bottom:20px} .amendment {margin-bottom:20px;margin-left:20px;border:2px solid #ebe9e8;padding-left:10px;width:30%;min-width:200px;padding-bottom:10px} .bill-title {color:black;background-color:#ffffff;padding-left:20px;} hr {color:#006e46;} .main-heading {padding-left:20px;padding-top:20px;}.main-summary {padding:0 0 10px 20px} .num-info {border-bottom: 1px dotted #ebe9e8;} .bill-reminder {text-align:right;color:#4d4d4d;font-size:10px;padding-right:5px;}</style>
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
                    </div>
                </div>
                
                <xsl:for-each-group select="item" group-by="bill">
                    <xsl:variable name="bill-grouping-key" select="current-grouping-key()"/>
                    <xsl:variable name="current-group-var" select="current-group()"/>
                    <!--## BILL ##-->
                    <div class="bill" id="{lower-case(replace(current-grouping-key(), ' ', '-'))}">
                        
                        <!-- Add bill title as heading -->
                        <h1 class="bill-title"><xsl:value-of select="current-grouping-key()"/></h1>
                        
                        <!--## AMDT NO ##-->
                        
                        <!-- For each amendment number in the matching FrameMaker XML file... -->
                        <xsl:for-each select="$todays-papers[normalize-space(descendant::STText) = $bill-grouping-key]/descendant::*[local-name()='Amendment.Number']">
                            <xsl:variable name="current-amdt" select="."/>
                            
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
                                        <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::names-to-add/matched-names/name) > 0">
                                            <div class="names-to-add">
                                                <h4>Names to add</h4>
                                                <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::names-to-add/descendant::name">
                                                    <div class="name">
                                                        <span>
                                                            <!-- If name does not match MNIS, add highlight -->
                                                            <xsl:if test="not(. = $mnis-name/Member/DisplayAs)">
                                                                <xsl:attribute name="style">
                                                                    <xsl:text>background-color: #FAA0A0</xsl:text>
                                                                </xsl:attribute>
                                                            </xsl:if>
                                                            
                                                            <!-- Link each name back to item on Added Names page -->
                                                            <a title="{concat('Dashboard ID:', ancestor::names-to-add/preceding-sibling::dashboard-id)}" href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', ancestor::names-to-add/preceding-sibling::dashboard-id)}" style="text-decoration: none;color:black"><xsl:value-of select="."/></a>
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
                                                <h5 style="margin-bottom:5px">Comments on dashboard</h5>
                                                <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::comments/p">
                                                    <p title="{concat('Dashboard ID:', parent::comments/@dashboard-id)}" style="font-size:smaller;color:#4d4d4d;">
                                                        <i><xsl:value-of select="."/></i>
                                                    </p>
                                                </xsl:for-each>
                                            </div>
                                        </xsl:if>
                                    </div><!-- End of amendment div -->
                                </xsl:for-each-group>
                                    
                                    
                                </xsl:for-each>
                                
                    </div>
                </xsl:for-each-group>
            </body>
        </html>
    </xsl:template>
    
    <xsl:template name="amdt-proc">
        
    </xsl:template>
    
    <!--<xsl:template match="name">
        <xsl:variable name="context-bill"/>
        <name>
            <xsl:if test=".=preceding::name[ancestor::names-to-add/preceding-sibling::bill = $context/ancestor::names-to-add/preceding-sibling::bill][ancestor::names-to-add/preceding-sibling::numbers/matched-numbers/amd-no=$context/ancestor::names-to-add/preceding-sibling::numbers/matched-numbers/amd-no]">
                <xsl:attribute name="class"><xsl:text>duplicate</xsl:text></xsl:attribute>
            </xsl:if>
            <xsl:value-of select="."/>
        </name>
    </xsl:template>-->
    
</xsl:stylesheet>