<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
    xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
    xmlns:georss="http://www.georss.org/georss"
    xmlns:gml="http://www.opengis.net/gml"
    xmlns:saxon="http://saxon.sf.net/"
    xml:base="https://hopuk.sharepoint.com/sites/bct-ppu/_api/"
    exclude-result-prefixes="xs m d georss gml"
    xpath-default-namespace="http://www.w3.org/2005/Atom"
    version="2.0">
    
    <!-- saxon:next-in-chain="post-processing-html.xsl" -->
    
    <xsl:output method="xml" encoding="UTF-8" />
    
    <xsl:template match="/">
        <root>
            <downloaded><xsl:value-of select="format-dateTime(feed/updated, '[FNn] [D1] [MNn], [H1]:[m01]')"/></downloaded>
            <xsl:apply-templates select="*"/>
        </root>
    </xsl:template>
    
    <xsl:template match="id|category|link|title|updated|author|name"/>
    
    <xsl:template match="feed|entry|content">
        <xsl:apply-templates select="*"/>
    </xsl:template>
    
    <xsl:template match="m:properties">
        <item>
            <xsl:apply-templates select="*[self::d:Amendments|self::d:Names|self::d:Id|self::d:Bill|self::d:Comments|self::d:Namestoremove]"/>
        </item>
    </xsl:template>
    
    <xsl:template match="d:Bill">
        <bill><xsl:value-of select="."/></bill>
    </xsl:template>
    
    <xsl:template match="d:Id">
        <dashboard-id><xsl:value-of select="."/></dashboard-id>
    </xsl:template>
    
    <!-- Amendment numbers -->
    <xsl:template match="d:Amendments">
        <numbers>
            <original-string><xsl:value-of select="normalize-space(.)"/></original-string>
            <!-- Matching amendment numbers using tokenize... -->
            <matched-numbers>
                <xsl:for-each select="tokenize(., '(\n|,|;| and | &amp; )')">
                    <xsl:choose>
                        <!--<xsl:when test="matches(., '')"/>-->
                        <xsl:when test="matches(., '(&#x2d;|&#x2014;|&#x2015;|&#x2010;|&#x2011;|&#xad;|&#x2012;|&#x2013;|&#x2212;| to )')">
                            <xsl:choose>
                                <!-- Double check test regex and analyze-string regex -->
                                <!-- Add colon, semi-colon,... -->
                                <xsl:when test="matches(., '(NC|Nc|New Clause|New Clauses|New clause|New clauses)')">
                                    <xsl:analyze-string select="." regex="(NC|Nc|nc|New Clause|New Clauses|New clause|New clauses):?\s?([0-9]{{1,3}})\s?(&#x2d;|&#x2014;|&#x2015;|&#x2010;|&#x2011;|&#xad;|&#x2012;|&#x2013;|&#x2212;| to )\s?(NC|nc|Nc)?([0-9]{{1,3}})">
                                        <xsl:matching-substring>
                                            <xsl:for-each select="xs:integer(regex-group(2)) to xs:integer(regex-group(5))">
                                                    <amd-no><xsl:value-of select="concat('NC', .)"/></amd-no>
                                            </xsl:for-each>
                                        </xsl:matching-substring>
                                        
                                    </xsl:analyze-string>
                                </xsl:when>
                                
                                <!-- Range of NSs -->
                                <xsl:when test="matches(., '(NS|Ns|New Clauses|New clause|New clauses)')">
                                    <xsl:analyze-string select="." regex="(NS|Ns|ns|New Schedule|New Schedules|New schedule|New schedules):?\s?([0-9]{{1,3}})\s?(&#x2d;|&#x2014;|&#x2015;|&#x2010;|&#x2011;|&#xad;|&#x2012;|&#x2013;|&#x2212;| to )\s?(NS|ns|Ns)?([0-9]{{1,3}})">
                                        <xsl:matching-substring>
                                            <xsl:for-each select="xs:integer(regex-group(2)) to xs:integer(regex-group(5))">
                                                    <amd-no><xsl:value-of select="concat('NS', .)"/></amd-no>
                                            </xsl:for-each>
                                        </xsl:matching-substring>
                                        
                                    </xsl:analyze-string>
                                </xsl:when>
                                
                                <!-- Range of amdts preceded by "Amendment" etc -->
                                <xsl:when test="matches(., '(A|Amendment|Amendments|Amdt|Amdts)')">
                                    <xsl:analyze-string select="." regex="(A|Amendment|Amendments|Amdt|Amdts):?\s?([0-9]{{1,3}})\s?(&#x2d;|&#x2014;|&#x2015;|&#x2010;|&#x2011;|&#xad;|&#x2012;|&#x2013;|&#x2212;|to)\s?(A|Amendment|Amendments|Amdt|Amdts)?\s?([0-9]{{1,3}})">
                                        <xsl:matching-substring>
                                            <xsl:for-each select="xs:integer(regex-group(2)) to xs:integer(regex-group(5))">
                                                    <amd-no><xsl:value-of select="."/></amd-no>
                                            </xsl:for-each>
                                        </xsl:matching-substring>
                                    </xsl:analyze-string>
                                </xsl:when>
                                
                                <!-- Range of amdts without prefix -->
                                <xsl:otherwise>
                                    <xsl:analyze-string select="." regex="([0-9]{{1,3}})\s?(&#x2d;|&#x2014;|&#x2015;|&#x2010;|&#x2011;|&#xad;|&#x2012;|&#x2013;|&#x2212;|to)\s?([0-9]{{1,3}})">
                                        <xsl:matching-substring>
                                            <xsl:for-each select="xs:integer(regex-group(1)) to xs:integer(regex-group(3))">
                                                    <amd-no><xsl:value-of select="."/></amd-no>
                                            </xsl:for-each>
                                        </xsl:matching-substring>
                                    </xsl:analyze-string>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when><!-- end amendment ranges -->
                        
                        <!-- When amendments are preceded by "A" etc. -->
                        <xsl:when test="matches(., '(A|Amendment|Amendments|Amdt|amdt):?\s?[0-9]{1,3}')">
                            <xsl:analyze-string select="." regex="(A|Amendment|Amendments|Amdt|amdt):?\s?([0-9]{{1,3}})">
                                <xsl:matching-substring>
                                    <amd-no><xsl:value-of select="regex-group(2)"/></amd-no>
                                </xsl:matching-substring>
                            </xsl:analyze-string>
                        </xsl:when>
                        
                        <!-- When NCs are preceded by "NC" etc. -->
                        <xsl:when test="matches(., '(NC|New Clause|New clause|new clause):?\s?([0-9]{1,3})')">
                            <xsl:analyze-string select="." regex="(NC|New Clause|New clause|new clause)\s?([0-9]{{1,3}})">
                                <xsl:matching-substring>
                                    <amd-no><xsl:value-of select="concat('NC', regex-group(2))"/></amd-no>
                                </xsl:matching-substring>
                                
                            </xsl:analyze-string>
                        </xsl:when>
                        
                        <xsl:when test="matches(.,'(NS|New Schedule|New schedule|new schedule):?\s?([0-9]{1,3})')">
                            <xsl:analyze-string select="." regex="(NS|New Schedule|New schedule|new schedule):?\s?([0-9]{{1,3}})">
                                <xsl:matching-substring>
                                    <amd-no><xsl:value-of select="concat('NS', regex-group(2))"/></amd-no>
                                </xsl:matching-substring>
                            </xsl:analyze-string>
                            
                        </xsl:when>
                        
                        <xsl:when test=".=''"/>
                        
                        <xsl:otherwise>
                            <xsl:analyze-string select="." regex="([0-9]{{1,3}})">
                                <xsl:matching-substring>
                                    <amd-no><xsl:value-of select="regex-group(1)"/></amd-no>
                                </xsl:matching-substring>
                            </xsl:analyze-string>
                            
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </matched-numbers>
            
            <!-- Matching amendment numbers using analyze-string only -->
            <!--<matched-numbers>
                <xsl:analyze-string select="normalize-space(.)" regex="(NC|NS)?(\s)?([0-9]{{1,3}})(-?(NC|NS)?\s?[0-9]{{1,3}})?">
                    <xsl:matching-substring>
                        <amd-no><xsl:value-of select="concat(regex-group(1), regex-group(3), regex-group(4))"/></amd-no>
                    </xsl:matching-substring>
                </xsl:analyze-string>
            </matched-numbers>-->
            
            <!-- THis needs to be updated, not sure it is still outputting the truth! -->
            <unmatched-numbers-etc>
                <xsl:analyze-string select="normalize-space(.)" regex="(NC|NS)?(\s)?([0-9]{{1,3}})(-?(NC|NS)?\s?[0-9]{{1,3}})?">
                    <xsl:non-matching-substring>
                        <xsl:value-of select="."/>
                    </xsl:non-matching-substring>
                </xsl:analyze-string>
            </unmatched-numbers-etc>
        </numbers>
    </xsl:template>
    
    
    
    <!-- Names to add -->
    <xsl:template match="d:Names[not(@m:null='true')]">
        <names-to-add>
            <original-string><xsl:value-of select="normalize-space(.)"/></original-string>
            <matched-names>
                <xsl:choose>
                    <xsl:when test="matches(., '(\n|,| and | &amp; )')">
                        <xsl:for-each select="tokenize(., '(\n|,| and | &amp; )')">
                            <xsl:choose>
                                <xsl:when test=".=''"/>
                                <xsl:otherwise>
                                    <xsl:analyze-string select="." regex="^\s?(&#x2022;|&#x2d;|&#x2014;|&#x2015;|&#x2010;|&#x2011;|&#xad;|&#x2012;|&#x2013;|&#x2212;)?\s?(.+[^ MP])">
                                        <xsl:matching-substring>
                                            <name><xsl:value-of select="regex-group(2)"/></name>
                                        </xsl:matching-substring>
                                    </xsl:analyze-string>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <name><xsl:value-of select="normalize-space(.)"/></name>
                    </xsl:otherwise>
                </xsl:choose>
                
            </matched-names>
        </names-to-add>
    </xsl:template>
    
    
    <xsl:template match="d:Namestoremove">
        <names-to-remove>
            <xsl:choose>
                <xsl:when test="@m:null='true'">
                    <xsl:text>None.</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <original-string><xsl:value-of select="normalize-space(.)"/></original-string>
                    <matched-names>
                        <xsl:choose>
                            <xsl:when test="matches(., '(\n|,| and | &amp;)')">
                                <xsl:for-each select="tokenize(., '(\n|,| and | &amp; )')">
                                    <name><xsl:value-of select="normalize-space(.)"/></name>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:otherwise>
                                <name><xsl:value-of select="."/></name>
                            </xsl:otherwise>
                        </xsl:choose>
                    </matched-names>
                </xsl:otherwise>
            </xsl:choose>
        </names-to-remove>
    </xsl:template>
    
    <xsl:template match="d:Comments[not(@m:null)]">
        <comments dashboard-id="{following-sibling::d:ID}">
            <xsl:choose>
                <xsl:when test="matches(., '\n')">
                    <xsl:for-each select="tokenize(., '\n')">
                        <p><xsl:value-of select="."/></p>
                    </xsl:for-each>
                </xsl:when>
                <xsl:otherwise>
                    <p><xsl:value-of select="."/></p>
                </xsl:otherwise>
            </xsl:choose>
        </comments>
    </xsl:template>
    
</xsl:stylesheet>