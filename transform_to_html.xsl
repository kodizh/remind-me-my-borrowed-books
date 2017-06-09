<?xml version="1.0"?>

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
  <html>
    <head><meta charset=\"UTF-8\"/>
  </head>
  <body>
    <div class=\"loans\">
      <div>Pourquoi reçois-je ce message ?</div>
      <ul>
        <xsl:for-each select="/sending-rules/*">
          <xsl:if test="due_date"><li>Des livres sont à rendre dans <xsl:value-of select="due_date"/> jour(s)</li></xsl:if>
          <xsl:if test="day"><li>Nous sommes <xsl:value-of select="day"/>, et <xsl:value-of select="day"/> est le jour du mémo !</li></xsl:if>
          <xsl:if test="list-change"><li>La liste des livres a changé depuis hier</li></xsl:if>
        </xsl:for-each>
      </ul>
    </div>

    <div style=\"display: inline-block;\">
      <xsl:for-each select="loans-set">
        <xsl:for-each select="loan">
          <xsl:value-of select="owner"/>
          <!-- the background attribute changes according to the owner -->
          <li class=\"book\" style=\"margin-left: 1em; padding-right: 2px; background: linear-gradient(to right, rgba(255,0,0,0) 99%, #3399ff)";>
            <b><xsl:value-of select="title"/></b>,
            <i><xsl:value-of select="author"/></i>
            <!-- only when changing owner -->
            <div style=\"float: right; clear: right; margin-left: 2em; color: grey; font-size: small; font-style: italic;\"><xsl:value-of select="owner"/></div>
          </li>
        </xsl:for-each>
      </xsl:for-each>
    </div>

    <div style=\"color: grey; font-size: 75%; border: 1px solid lightgrey; margin-bottom: 1em;\">
      <div style=\"background: darkgrey; color: white;\">Statistiques</div>
      <div style=\"display: inline-block; margin-left: 2em; vertical-align: top;\">
        Nombre de livres empruntés :
        <ul>
          <li style=\"font-weight: bold\">Total des livres : <xsl:value-of select="/stats/total"/></li>
          <xsl:for-each select="/stats/person">
            <li style=\"font-weight: bold\">Sur la carte d'<xsl:for-each select="name"/> : <xsl:for-each select="total"/></li>
          </xsl:for-each>
        </ul>
      </div>"

      <div style=\"display: inline-block; margin-left: 2em; vertical-align: top;\">
        Nombre de livres à rendre :
        <ul>
          <xsl:for-each select="/stats/date">
            <li>dans <xsl:for-each select="days-left"/> jours : <xsl:for-each select="total"/></li>
          </xsl:for-each>
        </ul>
      </div>
    </div>"

    <div style=\"color: grey; font-size: 75%; border: 1px solid lightgrey;\">
      <div style=\"background: darkgrey; color: white;\">Mes conditions d'envoi</div>
      <ul>
        <xsl:for-each select="/rules/user">
          <xsl:if select="list-change"><li>la liste des livres a changé depuis le dernier envoi</li></xsl:if>
          <xsl:if select="due-date">
            <li>des livres sont à rendre :
              <ul>
                <xsl:for-each select="due-date">
                  <xsl:if select="inf"><li>dans moins de {} jours.</li></xsl:if>
                  <xsl:if select="inf"><li>dans exactement {} jours.</li></xsl:if>
                </xsl:for-each>
              </ul>
            </li>
          </xsl:if>
          <xsl:if select="weekday">
            <li>Chaque 
              <ul>
                <xsl:for-each select="day">
                  <xsl:value-of select="text()"/>
                </xsl:for-each>
              </ul>
            </li>
          </xsl:if>
        </xsl:for-each>
      </ul>
    </div>
  </body>
</html>
</xsl:template>

</xsl:stylesheet> 
