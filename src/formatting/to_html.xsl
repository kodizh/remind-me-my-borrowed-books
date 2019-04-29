<?xml version="1.0"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/loan-data">
<html>
  <head>
    <meta charset="UTF-8"/>
    <style>
      .loansset {
        display:         inline-block;
      }
      .book {
        margin-left:     1em;
        padding-right:   2px;
        list-style:      none;
      }
      .book input {
        height:          1em;
        cursor:          pointer;
        margin-right:    5px;
        margin-bottom:   0;
        padding-bottom:  0;
      }
      .ownername {
        float:           right;
        clear:           right;
        margin-left:     2em;
        color:           grey;
        font-size:       small;
        font-style:      italic;
      }
      .statsblock {
        color:           grey;
        font-size:       x-small;
        border:          1px solid lightgrey;
        margin-bottom:   1em;
      }
      .statstitle {
        font-style:      italic;
        font-size:       small;
        padding:         .1em 0 .1em .5em;
        background:      darkgrey;
        color:           white;
      }
      .statscontent {
        display:         inline-block;
        margin-left:     2em;
        vertical-align:  top;
      }
      .sendingrulesblock {
        color:           grey;
        font-size:       x-small;
        border:          1px solid lightgrey;
      }
      .sendingrulescontent {
        font-style:      italic;
        font-size:       small;
        padding:         .1em 0 .1em .5em;
        background:      darkgrey;
        color:           white;
      }
      .faultblock {
        font-weight:     bold;
      }
      .faultcontent {
        margin-left:     2em;
        font-weight:     bold;
      }
    </style>
  </head>
  <body>
    <div class="loans">
      <div>Pourquoi reçois-je ce message ?</div>
      <ul>
        <!-- Displays the rules that matched the user-based sending rules. For each rule the @value attribute
             means that the rule has matched.
             – Remaining days rule that is not followed by any other active remaining days rule (this avoid
               duplicates, and it means that only the last one is displayed)
             – The current week of the day
             – The list of books has changed
        -->
        <xsl:apply-templates select="sending-rules/days-left[@value and not(@value = following-sibling::days-left/@value)] | sending-rules/weekday[@value] | sending-rules/list-change[@value]"/>
      </ul>
    </div>

    <div class="loansset">
      <!-- A loan-set is a set of loans to give back at the same date -->
      <xsl:apply-templates select="loan-set"/>
    </div>

    <!-- Statistics and ALL sending rules for this message -->
    <xsl:apply-templates select="stats|sending-rules"/>
  </body>
</html>
</xsl:template>

<xsl:template match="loan-set">
  <div>
    <b><xsl:value-of select="days-left"/> jours restants</b> (retour le <xsl:value-of select="return-date"/>)
    <ul>
      <xsl:apply-templates select="loan"/>
    </ul>
  </div>
</xsl:template>

<xsl:template match="loan">
  <xsl:variable name="owner" select="@owner"/>
  <li class="book">
    <xsl:attribute name="style">
      background: linear-gradient(to right, rgba(255,0,0,0) 99%, <xsl:value-of select="document('external_variables.xml')//owner-colour-list/*[@owner=$owner]"/>);
    </xsl:attribute>
    <input type="checkbox">
      <b><xsl:value-of select="title"/></b>, <i><xsl:value-of select="author"/></i>
      <!-- When the owner has several loans in this set, only shows his name next to the first loan -->
      <xsl:if test="not(@owner = preceding-sibling::loan/@owner)">
        <div class="ownername"><xsl:value-of select="$owner"/></div>
      </xsl:if>
    </input>
  </li>
</xsl:template>

<!-- General statistics about the current loans -->
<xsl:template match="stats">
  <div class="statsblock" >
    <div class="statstitle" >Statistiques</div>
    <div class="statscontent" >
      Nombre de livres empruntés :
      <ul>
        <xsl:apply-templates select="total|user"/>
      </ul>
    </div>

    <div class="statscontent">
      Nombre de livres à rendre :
      <ul>
        <xsl:apply-templates select="days-left"/>
      </ul>
    </div>
  </div>
</xsl:template>

<!-- Shows the sending rule that triggers the sending of a message for this user -->
<xsl:template match="sending-rules">
  <div class="sendingrulesblock">
    <div class="sendingrulescontent">Mes conditions d'envoi</div>
    <ul>
      <li>Chaque
        <xsl:for-each select="weekday">
          <b><xsl:value-of select="text()"/></b>,
        </xsl:for-each>
      </li>
      <li>Des livres sont à rendre :
        <ul>
          <xsl:for-each select="days-left">
            <xsl:if test="@type='inf'"><li>dans <b>moins de <xsl:value-of select="."/> jours</b>.</li></xsl:if>
            <xsl:if test="@type='eq'"><li>dans <b>exactement <xsl:value-of select="."/> jours</b>.</li></xsl:if>
          </xsl:for-each>
        </ul>
      </li>
      <xsl:apply-templates select="list-change"/>
    </ul>
  </div>
</xsl:template>

<xsl:template match="sending-rules/days-left">
  <li>Des livres sont à rendre dans <xsl:value-of select="@value"/> jour(s)</li>
</xsl:template>

<xsl:template match="weekday">
  <li>Nous sommes <xsl:value-of select="text()"/>, et <xsl:value-of select="text()"/> est le jour du mémo !</li>
</xsl:template>

<xsl:template match="list-change">
  <li>La liste des livres a changé depuis le dernier envoi</li>
</xsl:template>

<xsl:template match="total">
  <li>Total des livres : <b><xsl:value-of select="text()"/></b></li>
</xsl:template>

<xsl:template match="user">
  <li>Sur la carte d'<xsl:value-of select="@name"/> : <b><xsl:value-of select="text()"/></b></li>
</xsl:template>

<xsl:template match="stats/days-left">
  <li>dans <xsl:value-of select="@days"/> jours : <b><xsl:value-of select="text()"/></b></li>
</xsl:template>

<xsl:template match="/error">
<html>
  <head>
    <meta charset="UTF-8"/>
  </head>
  <body>
    <div class="loans">
      <div>Pourquoi reçois-je ce message ?</div>
      <ul>
        <li>
          <div class="faultblock">Error: a fault was detected during the program execution.</div>
          <div>The daily library remainder could not be sent to the selected recipients.</div>
        </li>
      </ul>
      <div>Exception description:</div>
      <div class="faultcontent"><xsl:value-of select="description"/></div>
    </div>
  </body>
</html>
</xsl:template>

</xsl:stylesheet>
