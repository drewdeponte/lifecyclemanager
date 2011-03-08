<?cs
# Copyright 2007-2008 Lifecycle Manager Development Team
# http://www.insearchofartifice.com/lifecyclemanager/wiki/DevTeam
#
# This file is part of Lifecycle Manager.
#
# Lifecycle Manager is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lifecycle Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lifecycle Manager.  If not, see
# <http://www.gnu.org/licenses/>.
?>

<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs def:create_link(rep_req, link_req) ?>
    <a href="<?cs var: link_requirement_href ?>/<?cs var: $link_req  ?>">
        <?cs var: $rep_req ?>
    </a>
<?cs /def ?>

<div id="ctxtnav" class="nav">
 <h2>Report Navigation</h2>
 <ul><li class="first"><?cs
   if:chrome.links.up.0.href ?><a href="<?cs
    var:chrome.links.up.0.href ?>">Available Reports</a><?cs
   else ?>Available Reports<?cs
  /if ?></li><?cs
  if:report.query_href ?><li class="last"><a href="<?cs
   var:report.query_href ?>">Custom Query</a></li><?cs
  /if ?>
  <?cs
    if:report.add_requirement_href ?><li class="last"><a href="<?cs
      var:report.add_requirement_href ?>">Add Requirement</a></li><?cs
    /if ?>
 </ul>
</div>

<h1>Timeline of Changes</h1>

<div class="debug"><?cs var: debug ?></div>

<script type="text/javascript">
  var tl;
  function onLoad() {
    var eventSource = new Timeline.DefaultEventSource();
    
    var theme = Timeline.ClassicTheme.create();
    theme.event.label.width = 150; // px
    theme.event.bubble.width = 250;
    theme.event.bubble.height = 200;
    theme.ether.backgroundColors.unshift("white");
    
    var bandInfos = [
      Timeline.createBandInfo({
          eventSource:    eventSource,
          date:           "<?cs var: current_time ?>",
          width:          "70%", 
          intervalUnit:   Timeline.DateTime.DAY, 
          intervalPixels: 100,
          theme:          theme
      }),
      Timeline.createBandInfo({
          showEventText:  false,
          trackHeight:    0.3,
          trackGap:       0.2,
          eventSource:    eventSource,
          date:           "<?cs var: current_time ?>",
          width:          "10%", 
          intervalUnit:   Timeline.DateTime.WEEK, 
          intervalPixels: 200,
          theme:          theme,
          overview:       true
      }),
      Timeline.createBandInfo({
          showEventText:  false,
          trackHeight:    0.3,
          trackGap:       0.2,
          eventSource:    eventSource,
          date:           "<?cs var: current_time ?>",
          width:          "10%", 
          intervalUnit:   Timeline.DateTime.MONTH, 
          intervalPixels: 600,
          theme:          theme,
          overview:       true
      }),
      Timeline.createBandInfo({
          showEventText:  false,
          trackHeight:    0.3,
          trackGap:       0.2,
          eventSource:    eventSource,
          date:           "<?cs var: current_time ?>",
          width:          "10%", 
          intervalUnit:   Timeline.DateTime.YEAR, 
          intervalPixels: 1000,
          theme:          theme,
          overview:       true
      })
    ];
    
    bandInfos[1].syncWith = 0;
    bandInfos[1].highlight = true;
    bandInfos[2].syncWith = 0;
    bandInfos[2].highlight = true;
    bandInfos[3].syncWith = 0;
    bandInfos[3].highlight = true;
    
    tl = Timeline.create(document.getElementById("timeline"), bandInfos);
    Timeline.loadXML("<?cs var: timeline_data_url ?>", function(xml, url) { eventSource.loadXML(xml, url); });
  }

  var resizeTimerID = null;
  function onResize() {
      if (resizeTimerID == null) {
          resizeTimerID = window.setTimeout(function() {
              resizeTimerID = null;
              tl.layout();
          }, 500);
      }
  }

  addEvent(window, 'load', onLoad);
  addEvent(window, 'resize', onResize);
</script>

<div id="timeline" class="timeline-default" style="height: 400px; margin: 2em;"></div>

<?cs include "footer.cs" ?>