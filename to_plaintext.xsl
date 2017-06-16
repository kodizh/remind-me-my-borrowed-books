<?xml version="1.0"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" indent="yes"/>

<xsl:template match="/loan-data">

Pourquoi reçois-je ce message ?
<!-- Displays the rules that matched the user-based sending rules. For each rule the @value attribute
     means that the rule has matched.
     – Remaining days rule that is not followed by any other active remaining days rule (this avoid
       duplicates, and it means that only the last one is displayed)
     – The current week of the day
     – The list of books has changed
-->
<xsl:apply-templates select="sending-rules/days-left[@value and not(@value = following-sibling::days-left/@value)] | sending-rules/weekday[@value] | sending-rules/list-change[@value]"/>

<xsl:apply-templates select="loan-set"/>

<xsl:apply-templates select="stats|sending-rules"/>
</xsl:template>

<!-- A loan-set is a set of loans to give back at the same date -->
<xsl:template match="loan-set">

✔ <xsl:value-of select="days-left"/> jours restants (retour le <xsl:value-of select="return-date"/>)
  <xsl:apply-templates select="loan"/>
</xsl:template>

<xsl:template match="loan">
  <xsl:variable name="owner" select="@owner"/>
<!-- When the owner has several loans in this set, only shows his name next to the first loan -->
  – <xsl:value-of select="title"/>, <xsl:value-of select="author"/><xsl:if test="not(@owner = preceding-sibling::loan/@owner)">           — <xsl:value-of select="$owner"/></xsl:if>
</xsl:template>

<!-- General statistics about the current loans -->
<xsl:template match="stats">
  
Statistiques :
  – Nombre de livres empruntés :<xsl:apply-templates select="total|user"/>

  – Nombre de livres à rendre :<xsl:apply-templates select="days-left"/>
</xsl:template>

<!-- Shows the sending rule that triggers the sending of a message for this user -->
<xsl:template match="sending-rules">

Mes conditions d'envoi :
  – Chaque <xsl:for-each select="weekday"><xsl:value-of select="text()"/>, </xsl:for-each>
  – Des livres sont à rendre :
<!----><xsl:for-each select="days-left">
<!--  --><xsl:if test="@type='inf'">    – dans moins de <xsl:value-of select="."/> jours.
<!--  --></xsl:if>
<!--  --><xsl:if test="@type='eq'">    – dans exactement <xsl:value-of select="."/> jours.
<!--  --></xsl:if>
<!----></xsl:for-each>
  <xsl:apply-templates select="list-change"/>
</xsl:template>

<xsl:template match="sending-rules/days-left">  – Des livres sont à rendre dans <xsl:value-of select="@value"/> jour(s)
</xsl:template>

<xsl:template match="weekday">  – Nous sommes <xsl:value-of select="text()"/>, et <xsl:value-of select="text()"/> est le jour du mémo !
</xsl:template>

<xsl:template match="list-change">
  – La liste des livres a changé depuis le dernier envoi
</xsl:template>

<xsl:template match="total">
    – Total des livres : <xsl:value-of select="text()"/>
</xsl:template>

<xsl:template match="user">
    – Sur la carte d'<xsl:value-of select="@name"/> : <xsl:value-of select="text()"/>
</xsl:template>

<xsl:template match="stats/days-left">
    – dans <xsl:value-of select="@days"/> jours : <xsl:value-of select="text()"/>
</xsl:template>

</xsl:stylesheet> 
