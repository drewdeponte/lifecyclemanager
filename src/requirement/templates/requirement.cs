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

      <div id="ctxtnav" class="nav">
        <h2>Requirement Navigation</h2><?cs
        with:links = chrome.links ?><?cs
        if:len(links.prev) || len(links.up) || len(links.next) ?><ul><?cs
          if:len(links.prev) ?>
          <li class="first<?cs if:!len(links.up) && !len(links.next) ?> last<?cs /if ?>">
	    &larr; <a href="<?cs var:links.prev.0.href ?>" title="<?cs
	      var:links.prev.0.title ?>">Previous Requirement</a>
          </li><?cs
          /if ?><?cs
          if:len(links.up) ?>
          <li class="<?cs if:!len(links.prev) ?>first<?cs /if ?><?cs
	    if:!len(links.next) ?> last<?cs /if ?>">
	    <a href="<?cs var:links.up.0.href ?>" title="<?cs
	      var:links.up.0.title ?>">Back to List of Requirements</a>
          </li><?cs
          /if ?><?cs
          if:len(links.next) ?>
          <li class="<?cs if:!len(links.prev) && !len(links.up) ?>first <?cs /if ?>last">
	    <a href="<?cs var:links.next.0.href ?>" title="<?cs
	      var:links.next.0.title ?>">Next Requirement</a> &rarr;
          </li><?cs
          /if ?></ul><?cs
        /if ?><?cs
        /with ?>
      </div>

      <div id="content">

        <div id="searchable">
        <h1>&lt;<?cs var:requirement.component ?>
          <?cs var:fp ?>
          <?cs var:object ?>&gt;</h1>
          <div id="requirement">
	    <div class="date">
	      <p title="<?cs var:requirement.created ?>">Created <?cs var:requirement.created_delta ?> ago</p><?cs
	      if:requirement.lastmod ?>
	      <p title="<?cs var:requirement.lastmod ?>">Last modified <?cs var:requirement.lastmod_delta ?> ago</p>
	      <?cs /if ?>
	    </div>
	    <h2 class="summary">&nbsp;</h2>
	    <table class="properties">
	      <tr>
	        <th id="h_creator">Created by:</th>
	        <td headers="h_creator"><?cs var:requirement.creator ?></td>
	      </tr>
	      <tr>
	        <?cs each:field = requirement.fields ?>
	        <?cs if:!field.skip ?>
	        <?cs set:num_fields = num_fields + 1 ?>
	        <?cs /if ?>
	        <?cs /each ?>
	        
	        <?cs set:idx = 0 ?>
	        <?cs each:field = requirement.fields ?>
	        <?cs if:!field.skip ?>
	        <?cs set:fullrow = field.type == 'textarea' ?>
	        <?cs if:fullrow && idx % 2 ?>
	        <th></th><td></td></tr><tr>
	        <?cs /if ?>
	        <th id="h_<?cs var:name(field) ?>"><?cs var:field.label ?>:</th>
	        <td<?cs if:fullrow ?> colspan="3"<?cs /if ?> headers="h_<?cs var:name(field) ?>">
	          <?cs var:requirement[name(field)] ?>
	        </td>
	        <?cs if:idx % 2 || fullrow ?></tr><tr><?cs elif:idx == num_fields - 1 ?><th></th><td></td><?cs /if ?>
	        <?cs set:idx = idx + #fullrow + 1 ?>
	        <?cs /if ?>
	        <?cs /each ?>
	      </tr>
	    </table>
	    <?cs if:requirement.description ?>
	    <form method="get" action="<?cs var:requirement.href ?>#comment" class="printableform">
	      <div class="description">
	        <h3 id="reqcomment:description">
	          <?cs if:trac.acl.REQUIREMENT_APPEND ?>
	          <span class="inlinebuttons">
		    <input type="hidden" name="replyto" value="description" />
		    <input type="submit" value="Reply" title="Reply, quoting this description" />
	          </span>
	          <?cs /if ?>
	          Description
	          <?cs if:requirement.description.lastmod ?>
	          <span class="lastmod" title="<?cs var:requirement.description.lastmod ?>">
		    (Last modified by <?cs var:requirement.description.author ?>)
	          </span>
	          <?cs /if ?>
	        </h3>
	        <?cs var:requirement.description.formatted ?>
	      </div>
	    </form>
	    <?cs /if ?>
          </div>



          <?cs def:commentref(prefix, cnum) ?>
          <a href="#reqcomment:<?cs var:cnum ?>"><small><?cs var:prefix ?><?cs var:cnum ?></small></a>
          <?cs /def ?>



          <?cs if:len(requirement.changes) ?><h2>Change History</h2>
          <div id="changelog">

	    <?cs each:change = requirement.changes ?>
            <form method="get" action="<?cs var:requirement.href ?>#comment" class="printableform">
	      <div class="change">
	        
	        <h3 <?cs if:change.cnum ?>id="reqcomment:<?cs var:change.cnum ?>"<?cs /if ?>>
	          
	          <?cs if:change.cnum ?>
	          
	          <?cs if:trac.acl.REQUIREMENT_APPEND ?>
	          
	          <span class="inlinebuttons">
		    <input type="hidden" name="replyto" value="<?cs var:change.cnum ?>" />
		      <input type="submit" value="Reply" title="Reply to comment <?cs var:change.cnum ?>" />
	          </span>
	          
	          <?cs /if ?>

	          <span class="threading">
                    
                    <?cs set:nreplies = len(requirement.replies[change.cnum]) ?>
                    <?cs if:nreplies || change.replyto ?>
                    (<?cs if:change.replyto ?>in reply to: 
                    
                    <?cs call:commentref('&uarr;&nbsp;', change.replyto) ?>
                    
                    <?cs if nreplies ?>; 
                    
                    <?cs /if ?>
                    
                    <?cs /if ?>
                    
                    <?cs if nreplies ?>
                    <?cs call:plural('follow-up', nreplies) ?>: 
                    
                    <?cs each:reply = requirement.replies[change.cnum] ?>
                    
                    <?cs call:commentref('&darr;&nbsp;', reply) ?>
                    <?cs /each ?>
                    <?cs /if ?>)
                    <?cs /if ?>
	          </span>
	          <?cs /if ?>
	          <?cs var:change.date ?> changed by <?cs var:change.author ?>
	        </h3><?cs
	        if:len(change.fields) ?>
	        <ul class="changes"><?cs
	          each:field = change.fields ?>
	          <li><strong><?cs var:name(field) ?></strong> <?cs
		    if:name(field) == 'attachment' ?><em><?cs var:field.new ?></em> added<?cs
		    elif:field.old && field.new ?>changed from <em><?cs
		      var:field.old ?></em> to <em><?cs var:field.new ?></em><?cs
		    elif:!field.old && field.new ?>set to <em><?cs var:field.new ?></em><?cs
		    elif:field.old && !field.new ?>deleted<?cs
		    else ?>changed<?cs
		    /if ?>.</li>
	          <?cs
	          /each ?>
	        </ul><?cs
	        /if ?>
	        <div class="comment"><?cs var:change.comment ?></div>
	      </div>
	    </form><?cs
	    /each ?>
          </div><?cs
          /if ?>

        </div> <!-- id=searchable -->

        <hr />

          <?cs if:trac.acl.REQUIREMENT_MODIFY ?>
          <form action="<?cs var:requirement.href ?>" method="post">
	    <hr />
	      <h3><a name="edit" onfocus="document.getElementById('comment').focus()">Add/Change &lt;<?cs
	    var:requirement.component ?>
	    <?cs var:fp ?>
	    <?cs var:object ?>&gt;</a></h3>
	    <?cs if:trac.authname == "anonymous" ?>
	    <div class="field">
	      <label for="author">Your email or username:</label><br />
	        <input type="text" id="author" name="author" size="40"
	          value="<?cs var:requirement.reporter_id ?>" /><br />
	    </div>
	    <?cs /if ?>
	    <div class="field">
	      <fieldset class="iefix">
	        <label for="comment">Comment (you may use <a tabindex="42" href="<?cs
		    var:trac.href.wiki ?>/WikiFormatting">WikiFormatting</a> here):</label><br />
	          <p><textarea id="comment" name="comment" class="wikitext" rows="10" cols="78"><?cs var:requirement.comment ?></textarea></p>
	      </fieldset><?cs
	      if requirement.comment_preview ?>
	      <fieldset id="preview">
	        <legend>Comment Preview</legend>
	        <?cs var:requirement.comment_preview ?>
	      </fieldset><?cs
	      /if ?>
	    </div>
	    <div id="ctxtnav" class="nav"></div>

	    <div id="content" class="requirement">

	      <fieldset>
                <legend>Change Properties</legend>
	        <table border="0">
	          <tr>
		    Enabled: <input type="checkbox" name="status" <?cs 
                      if:requirement.status != "disabled" ?>
            		      checked <?cs 
                      /if ?> /><?cs
                      if:requirement.status == "out-of-date" ?>
                        (out of date)<?cs
                      /if ?>
	          </tr>
	          <tr>
		    <td>
		      Component: <br /> 
		        <select disabled style="width: 150px; border: 1px solid gray;" class="addreqinpt" name="component_curr">
		          <?cs each: comp = components ?>
		          <option
			    <?cs if:comp == requirement.component ?>
			    selected
			    <?cs /if ?> 
			    ><?cs var:comp ?></option> 
		          <?cs /each ?>
		        </select>
		    </td>
		    <td>
		      Functional Primitive: <br />
		        <input disabled style="border: 1px solid gray;" class="addreqinpt" value="<?cs var:fp ?>" name="fp_curr" />
		    </td>
		    <td>
		      Object: <br />
		        <input disabled style="border: 1px solid gray;" class="addreqinpt" value="<?cs var:object ?>" name="object_curr" />
		    </td>
	          </tr>
	          <tr>
		    <td colspan="3">
		      Description: <br />
		        <textarea cols="78" rows="10" name="description" id="req_description" ><?cs var:requirement.description ?></textarea>
		    </td>
	          </tr>
	        </td>
	        </tr>
	        </table>
	      </fieldset>
	      <div class="buttons">
	        <input type="hidden" name="component" value="<?cs var:requirement.component ?>" />
	        <input type="hidden" name="fp" value="<?cs var:fp ?>" />
	        <input type="hidden" name="object" value="<?cs var:object ?>" />
	        <input type="hidden" name="ts" value="<?cs var:requirement.ts ?>" />
	        <input type="hidden" name="replyto" value="<?cs var:requirement.replyto ?>" />
	        <input type="hidden" name="cnum" value="<?cs var:requirement.cnum ?>" />
	        <input type="submit" value="Submit changes" />
	      </div>

          </form>
          <?cs /if ?><!---This ends the REQUIREMENT_MODIFY if--->
          <script type="text/javascript" src="<?cs
	    var:htdocs_location ?>js/wikitoolbar.js"></script>

      </div>
      <script type="text/javascript">
        addHeadingLinks(document.getElementById("searchable"), "Permalink to $id");
      </script>
    </div>

      <div id="graphs">
        <h3>Changes Over Time Graph<br>
	    (y-axis changes/x-axis time in 24 hour days)</h3>
        <h6>color legend: change gaps = blue, milestone due dates = red, unit markers = black</h6>
        <iframe src="<?cs var: graph_path ?><?cs var:requirement.component ?>-<?cs var:fp ?>-<?cs var:object 
?>/changes_over_time_86400" height="325" width="320" scrolling="auto" frameborder="0"></iframe>
        <hr />

          <h3>Changes Over Time Graph<br>
	      (y-axis changes/x-axis time in weeks)</h3>
        <h6>color legend: change gaps = blue, milestone due dates = red, unit markers = black</h6>
        <iframe src="<?cs var: graph_path ?><?cs var:requirement.component ?>-<?cs var:fp ?>-<?cs var:object 
?>/changes_over_time_604800" height="325" width="320" scrolling="auto" frameborder="0"></iframe>


        <hr />
          <h3>Assesment of Related Tickets Over a 12-Month Period <br />(includes tickets later re-opened for additional work)</h3>
          <h6>color legend: tasks = green, enhancements = blue, defects = red</h6>
          <iframe src="<?cs var: graph_path ?><?cs var:requirement.component ?>-<?cs var:fp ?>-<?cs var:object ?>/tickets_over_time" height="325" width="320" scrolling="auto" frameborder="0"></iframe>
       <hr />
     
      </div>

       

      <?cs include "footer.cs"?>
