<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    version="2.0">
    
    <xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" version="5"/>
    
    <xsl:variable name="todays-papers" select="collection('*.xml')/Amendments.Commons"/>
    <xsl:variable name="mnis-name" select="document('http://data.parliament.uk/membersdataplatform/services/mnis/members/query/House=Commons%7CIsEligible=true/')/Members"/>
    
    <xsl:template match="root">
        <html>
        <head>
            <title><xsl:value-of select="concat(current-date(), ' Added Names')"/></title>
            <style>html {font-family:Verdana, sans-serif;background-color:#c0c0c0} body {width:90%;background-color:#ffffff;margin-left:30px;} .bill,.header {margin:10px} .number-summary-count {margin-bottom:20px} .amendment {margin-bottom:20px}</style>
        </head>
        <body>
            <!-- Header section with main heading and selection of bills -->
            <div class="header">
                <div class="main-heading" style="text-align:center">
                    <h1>Added Names report <xsl:value-of select="format-dateTime(current-dateTime(),'[FNn] [D1] [MNn], [H1]:[m01]')"/></h1>
                </div>
                <p><xsl:value-of select="concat(count(distinct-values(item/bill)), ' papers have added names today, please select one to view:')"/></p>
            <!-- Create drop-down to select bill - work in progress -->
                <select>
                    <xsl:for-each-group select="item" group-by="bill">
                        <option>
                            <xsl:attribute name="value"><xsl:value-of select="lower-case(replace(current-grouping-key(), ' ', '-'))"/></xsl:attribute>
                            <xsl:value-of select="current-grouping-key()"/>
                        </option>
                    </xsl:for-each-group>
                </select>
            </div>
            <xsl:for-each-group select="item" group-by="bill">
                <!--## BILL ##-->
                <div class="bill">
                    <h1><xsl:value-of select="current-grouping-key()"/></h1>
                    <!--## SUMMARY OF AMDT NOs ##-->
                    <!--<div class="number-summary">
                        <!-\-<h2><xsl:text>Amendment numbers with added/removed names</xsl:text></h2>-\->
                        <div class="number-summary-count"><p>Amendments in this paper with names added/removed:<b><xsl:value-of select="count(distinct-values(current-group()/descendant::matched-numbers/amd-no))"/></b></p></div>
                        <div class="number-summary-list">
                            <p>Amendment numbers affected:</p>
                            <p><xsl:value-of select="distinct-values(current-group()/descendant::matched-numbers/amd-no)" separator=", "/></p>
                        </div>
                    </div>-->
                    <hr/>
                    <!--## AMDT NO ##-->
                    <xsl:for-each-group select="current-group()/descendant::matched-numbers" group-by="amd-no">
                    <!--<xsl:for-each-group select="current-group()/descendant::matched-numbers" group-by="amd-no">-->
                    <!--<xsl:for-each-group select="$todays-papers[descendant::STText = $bill-current-grouping-key]/descendant::Amendment.Number" group-by="amd-no">-->
<!--                        <xsl:sort select="$todays-papers[descendant::STText = $bill-current-grouping-key]/descendant::Amendment.Number"></xsl:sort>-->
                        <div class="amendment">
                            <div class="num-info">
                                <h2 class="amendment-number">
                                    <xsl:choose>
                                        <xsl:when test="not(matches(current-grouping-key(), '(NC|NS)'))">
                                            <xsl:value-of select="concat('Amendment ', current-grouping-key())"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:value-of select="current-grouping-key()"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                    
                                </h2>
                                <!--## Hide divs containing dashboard IDs for now -->
                                <!--<xsl:for-each select="distinct-values(current-group()/ancestor::numbers/preceding-sibling::dashboard-id)">
                                    <div class="dashboard-id"><a href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', .)}"><xsl:value-of select="."/></a></div>
                                </xsl:for-each>-->
                            </div>
                            
                            <!-- If there are names to add -->
                            <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::names-to-add/matched-names/name) > 0">
                            <div class="names-to-add">
                                <h4>Names to add</h4>
                                <!--<div class="total-names-to-add"><p><xsl:value-of select="concat(count(current-group()/ancestor::numbers/following-sibling::names-to-add/matched-names/name), ' names in total to add')"/></p></div>-->
                                
                                <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::names-to-add/descendant::name">
                                    <!--<xsl:variable name="group" select="."/>-->
                                    <!--### Remove extra div for now -->
                                    <!--<div class="name-info">-->
                                    
                                    
                                    <div class="name">
                                        <span>
                                            <xsl:if test="not(. = $mnis-name/Member/DisplayAs)">
                                                <xsl:attribute name="style">
                                                    <xsl:text>background-color: #FAA0A0</xsl:text>
                                                </xsl:attribute>
                                            </xsl:if>
                                            <a title="{concat('Dashboard ID:', ancestor::names-to-add/preceding-sibling::dashboard-id)}" href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', ancestor::names-to-add/preceding-sibling::dashboard-id)}" style="text-decoration: none;color:black"><xsl:value-of select="."/></a></span>
                                    </div>
                                    
                                        
                                        <!--### Hide divs containing dashboard ID links for now ###-->
                                        <!--<div class="dashboard-id"><a href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', ancestor::names-to-add/preceding-sibling::dashboard-id)}"><xsl:value-of select="ancestor::names-to-add/preceding-sibling::dashboard-id"/></a></div>-->
                                    <!--</div>-->
                                </xsl:for-each>
                                
                                
                                
                                <!-- Works but want to add attr to duplicate names -->
                                <!--<xsl:for-each select=".">
                                    <xsl:copy-of select="current-group()/ancestor::numbers/following-sibling::names-to-add/matched-names/name"/>
                                </xsl:for-each>-->
                            
                            </div>
                            </xsl:if>
                            
                            
                            
                            <!-- If there are names to remove -->
                            <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::names-to-remove/matched-names/name) > 0">
                                <div class="names-to-remove">
                                    <h4>Names to remove</h4>
                                    <div class="total-names-to-remove"><p><xsl:value-of select="concat(count(current-group()/ancestor::numbers/following-sibling::names-to-remove/matched-names/name), ' names in total to remove')"/></p></div>
                                    <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::names-to-remove/descendant::name">
                                        <div class="name">
                                            <span><a title="{concat('Dashboard ID:', ancestor::names-to-remove/preceding-sibling::dashboard-id)}" href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', ancestor::names-to-remove/preceding-sibling::dashboard-id)}"><xsl:value-of select="."/></a></span>
                                        </div>
                                    </xsl:for-each>
                                    
                                </div>
                            </xsl:if>
                            
                             <!-- If there are comments -->
                            <xsl:if test="count(current-group()/ancestor::numbers/following-sibling::comments/p) > 0">
                                <div class="comments">
                                    <h5 style="margin-bottom:5px">Comments on dashboard</h5>
                                    <xsl:for-each select="current-group()/ancestor::numbers/following-sibling::comments/p">
                                        <p title="{concat('Dashboard ID:', parent::comments/@dashboard-id)}" style="font-size:10pt"><!--<a href="{concat('https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID=', parent::comments/@dashboard-id)}"><xsl:value-of select="@dashboard-id"/></a>--> <i><xsl:value-of select="."/></i></p>
                                    </xsl:for-each>
                                </div>
                            </xsl:if>
                            
                        </div>
                        <hr/>
                    </xsl:for-each-group>
                </div>
            </xsl:for-each-group>
        </body>
            </html>
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