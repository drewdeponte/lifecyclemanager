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

<script type="text/javascript">
addEvent(window, 'load', function() { document.getElementById('component').focus()}); 
</script>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="ticket">
<h1><?cs var:title ?></h1>

<form id="newticket" method="post" action="<?cs var:trac.href.newrequirement ?>">
    <fieldset>
        <table border="0">
            <tr>
                <td>
                    Component: <br /> 
                    <select id="component" style="width: 150px; border: 1px solid gray;" class="addreqinpt" name="component">
                       <?cs each: comp = components ?>
                            <option><?cs var:comp ?></option> 
                       <?cs /each ?>
                    </select>
                </td>
                <td>
                    Functional Primitive: <br />
                    <input id="fp" style="border: 1px solid gray;" class="addreqinpt" name="fp" />

                    <div id="fp_autocomplete" class="autocomplete"></div>
                    <script type="text/javascript">
                    new Ajax.Autocompleter("fp", "fp_autocomplete", "<?cs var:trac.href.auto_complete ?>/fp", {parameters: '__FORM_TOKEN=<?cs var:form_token ?>'});
                    </script>
                </td>
                <td>
                   Object: <br />
                    <input id="object" style="border: 1px solid gray;" class="addreqinpt" name="object" />
                    <div id="object_autocomplete" class="autocomplete"></div>
                    <script type="text/javascript">
                    new Ajax.Autocompleter("object", "object_autocomplete", "<?cs var:trac.href.auto_complete ?>/object", {parameters: '__FORM_TOKEN=<?cs var:form_token ?>'});
                    </script>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    Description: <br />
                    <textarea cols="95" rows="10" name="description" id="req.description" ></textarea>
                </td>
            </tr>
            <tr>
                <td><input type="submit" value="Submit Requirement" />
            </tr>
        </table>
    </fieldset>
</form>

</div>


<?cs include "footer.cs" ?>
