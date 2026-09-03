import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PortfolioFormDialog } from './portfolio-form-dialog';

describe('PortfolioFormDialog', () => {
  let component: PortfolioFormDialog;
  let fixture: ComponentFixture<PortfolioFormDialog>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortfolioFormDialog],
    }).compileComponents();

    fixture = TestBed.createComponent(PortfolioFormDialog);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
