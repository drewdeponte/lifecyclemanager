
package main;

$ourtrac = 'http://www.insearchofartifice.com/lifecyclemanager/';

sub do_cmd_ourtrac {
    local ($content) = @_;

    ($index) = ($content =~ m/^<\#(\d+)\#/s);

    if($index =~ /\d+/)
    {
	($input, $rest) = ($content =~ m/<\#(??{$index})\#>(.*)<\#(??{$index})\#>(.*)/xs);
	return '<a href="'.$ourtrac.$input.'">'.$ourtrac.$input.'</a>'.$rest;
    }

    return $content;
}

sub do_cmd_ourwiki {
    local ($content) = @_;

    ($index) = ($content =~ m/^<\#(\d+)\#/s);

    if($index =~ /\d+/)
    {
	($input, $rest) = ($content =~ m/<\#(??{$index})\#>(.*)<\#(??{$index})\#>(.*)/xs);
	return '<a href="'.$ourtrac.'wiki/'.$input.'">'.$input.'</a>'.$rest;
    }

    return $content;
}

sub do_cmd_req {
    local ($content) = @_;
    
    ($index) = ($content =~ m/^<\#(\d+)\#>/s);
    
    if($index =~ /\d+/)
    {
	($component, $fp, $object, $rest) =
	    ($content =~ m/
				<\#(??{$index})\#>(.*)<\#(??{$index})\#>
				<\#(??{$index+1})\#>(.*)<\#(??{$index+1})\#>
				<\#(??{$index+2})\#>(.*)<\#(??{$index+2})\#>
				(.*)/xs);
	
	return '<a href="'.$ourtrac.'requirement/'.$component.'-'.$fp.'-'.$object.'">' .
	    '&lt;'.$component.' '.$fp.' '.$object.'&gt;' .
	    '</a>' .
	    $rest;
    }
    
    return $content;
}

sub do_cmd_nreq {
    local ($content) = @_;
    
    ($index) = ($content =~ m/^<\#(\d+)\#>/s);
    
    if($index =~ /\d+/)
    {
	($component, $fp, $object, $description, $rest) =
	    ($content =~ m/
				<\#(??{$index})\#>(.*)<\#(??{$index})\#>
				<\#(??{$index+1})\#>(.*)<\#(??{$index+1})\#>
				<\#(??{$index+2})\#>(.*)<\#(??{$index+2})\#>
				<\#(??{$index+3})\#>(.*)<\#(??{$index+3})\#>
				(.*)/xs);
	
	return '<a href="'.$ourtrac.'requirement/'.$component.'-'.$fp.'-'.$object.'">' .
	    '&lt;'.$component.' '.$fp.' '.$object.'&gt;' .
	    '</a>' .
	    ' - '.$description .
	    $rest;
    }
    
    return $content;
}

1;
