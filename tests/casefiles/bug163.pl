#!/usr/bin/perl -w -- 
#
# generated by wxGlade "faked test version"
#
# To get wxPerl visit http://www.wxperl.it
#

use Wx 0.15 qw[:allclasses];
use strict;

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade

package MyFrame;

use Wx qw[:everything];
use base qw(Wx::Frame);
use strict;

use Wx::Locale gettext => '_T';
sub new {
    my( $self, $parent, $id, $title, $pos, $size, $style, $name ) = @_;
    $parent = undef              unless defined $parent;
    $id     = -1                 unless defined $id;
    $title  = ""                 unless defined $title;
    $pos    = wxDefaultPosition  unless defined $pos;
    $size   = wxDefaultSize      unless defined $size;
    $name   = ""                 unless defined $name;

    # begin wxGlade: MyFrame::new
    $style = wxDEFAULT_FRAME_STYLE 
        unless defined $style;

    $self = $self->SUPER::new( $parent, $id, $title, $pos, $size, $style, $name );
    $self->{label_1} = Wx::StaticText->new($self, wxID_ANY, _T("Extraproperty example"));

    $self->__set_properties();
    $self->__do_layout();

    # end wxGlade
    return $self;

}


sub __set_properties {
    my $self = shift;
    # begin wxGlade: MyFrame::__set_properties
    $self->SetTitle(_T("MyFrame"));
    $self->{label_1}->SetFont(Wx::Font->new(40, wxDEFAULT, wxNORMAL, wxNORMAL, 0, ""));
    $self->{label_1}->SetFoobar(1);
    # end wxGlade
}

sub __do_layout {
    my $self = shift;
    # begin wxGlade: MyFrame::__do_layout
    $self->{sizer_1} = Wx::BoxSizer->new(wxVERTICAL);
    $self->{sizer_1}->Add($self->{label_1}, 1, wxALL, 5);
    $self->SetSizer($self->{sizer_1});
    $self->{sizer_1}->Fit($self);
    $self->Layout();
    # end wxGlade
}

# end of class MyFrame

1;

